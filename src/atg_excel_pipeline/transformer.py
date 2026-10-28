"""Transformation des lignes brutes et filtres métier (§10)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from atg_excel_pipeline.config import Settings
from atg_excel_pipeline.convert import (
    clean_text,
    is_blank,
    is_excel_error,
    parse_date,
    parse_integer,
    parse_number,
    parse_time_entree,
    parse_time_sortie,
)
from atg_excel_pipeline.parser import ParsedWorkbook, RawRow
from atg_excel_pipeline.quality import (
    MOTIF_DATE_ABSENTE_OU_INVALIDE,
    MOTIF_DATE_LIVRAISON_ABSENTE_OU_INVALIDE,
    MOTIF_PRODUIT_ABSENT,
    QualityReport,
)
from atg_excel_pipeline.schemas import ENTREE_COLUMNS, SORTIE_COLUMNS, FieldType, Flow, FlowSpec

ENTREE_DUP_KEYS = ("n_bon", "date_principale", "produit")
SORTIE_DUP_KEYS = ("n_bsl", "date_livraison", "produit")


@dataclass
class RejectedRow:
    source_row: int
    motif: str
    raw: dict[str, object]


@dataclass
class TransformedFile:
    parsed: ParsedWorkbook
    valid_rows: list[dict[str, object]] = field(default_factory=list)
    rejected_rows: list[RejectedRow] = field(default_factory=list)
    quality: QualityReport = field(default_factory=QualityReport)
    date_min: object | None = None
    date_max: object | None = None


def transform_workbook(parsed: ParsedWorkbook, settings: Settings) -> TransformedFile:
    result = TransformedFile(parsed=parsed)
    spec = parsed.spec
    for raw in parsed.rows:
        if _row_blank(raw):
            result.quality.rows_blank_skipped += 1
            continue
        result.quality.rows_read += 1
        converted, motif = _convert_row(raw, spec, settings, result.quality)
        if motif is not None:
            result.quality.rejected_rows += 1
            result.quality.add_motif(motif)
            result.rejected_rows.append(RejectedRow(raw.source_row, motif, dict(raw.bound)))
            continue
        converted["source_name"] = parsed.path.name
        converted["source_row"] = raw.source_row
        result.valid_rows.append(converted)
        result.quality.valid_rows += 1

    date_field = "date_principale" if spec.flow is Flow.ENTREE else "date_livraison"
    dates = [row[date_field] for row in result.valid_rows if row.get(date_field) is not None]
    if dates:
        result.date_min = min(dates)
        result.date_max = max(dates)

    keys = ENTREE_DUP_KEYS if spec.flow is Flow.ENTREE else SORTIE_DUP_KEYS
    result.quality.duplicate_rows = _count_duplicates(result.valid_rows, keys)
    return result


def _row_blank(raw: RawRow) -> bool:
    if raw.values and all(is_blank(v) for v in raw.values):
        return True
    return bool(raw.bound) and all(is_blank(v) for v in raw.bound.values())


def _convert_row(
    raw: RawRow,
    spec: FlowSpec,
    settings: Settings,
    quality: QualityReport,
) -> tuple[dict[str, object] | None, str | None]:
    if spec.flow is Flow.SORTIE:
        produit = clean_text(raw.bound.get("produit"))
        if produit is None:
            return None, MOTIF_PRODUIT_ABSENT

    converted: dict[str, object] = {}
    columns = spec.columns
    for column in columns:
        raw_value = raw.bound.get(column.field)
        value, kind = _convert_field(column.field_type, raw_value, spec.flow, settings)
        if kind == "cell":
            quality.cell_errors += 1
        elif kind == "conversion":
            quality.conversion_errors += 1
        converted[column.field] = value

        if column.required and column.field_type is FieldType.DATE and value is None:
            if spec.flow is Flow.ENTREE:
                return None, MOTIF_DATE_ABSENTE_OU_INVALIDE
            return None, MOTIF_DATE_LIVRAISON_ABSENTE_OU_INVALIDE

    return converted, None


def _convert_field(
    field_type: FieldType,
    raw_value: object,
    flow: Flow,
    settings: Settings,
) -> tuple[object, str | None]:
    if is_excel_error(raw_value):
        return None, "cell"
    if field_type is FieldType.TEXTE:
        return clean_text(raw_value), None
    if field_type is FieldType.NUMERIQUE:
        result = parse_number(raw_value)
        return result.value, result.error
    if field_type is FieldType.ENTIER:
        result = parse_integer(raw_value)
        return result.value, result.error
    if field_type is FieldType.DATE:
        result = parse_date(raw_value, dayfirst=settings.date_dayfirst)
        return result.value, result.error
    if field_type is FieldType.HEURE:
        if flow is Flow.ENTREE:
            result = parse_time_entree(raw_value)
        else:
            result = parse_time_sortie(raw_value)
        return result.value, result.error
    return None, "conversion"


def _count_duplicates(rows: list[dict[str, object]], keys: tuple[str, ...]) -> int:
    counter: Counter[tuple[object, ...]] = Counter()
    for row in rows:
        key = tuple(row.get(k) for k in keys)
        if all(part is None for part in key):
            continue
        counter[key] += 1
    return sum(count - 1 for count in counter.values() if count > 1)


def field_names(flow: Flow) -> tuple[str, ...]:
    columns = ENTREE_COLUMNS if flow is Flow.ENTREE else SORTIE_COLUMNS
    return tuple(c.field for c in columns)

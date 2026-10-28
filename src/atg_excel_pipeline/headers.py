"""Normalisation d'en-têtes et liaison par identité (en-tête, rang) + position."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from atg_excel_pipeline.schemas import ColumnSpec, FlowSpec


class StructureError(ValueError):
    """Fichier rejeté : structure d'en-têtes incompatible avec la spécification."""


def normalize_header(value: object) -> str:
    """NFKC, suppression de tout espace (U+00A0, \\n, \\r), casefold."""

    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    stripped = []
    for char in text:
        if char in {"\n", "\r", "\t", "\xa0"} or char.isspace():
            continue
        stripped.append(char)
    return "".join(stripped).casefold()


def find_header_row(
    first_column: list[object],
    spec: FlowSpec,
    *,
    max_rows: int = 200,
    allow_fallback: bool = False,
) -> int:
    """Retourne le numéro de ligne 1-based de l'en-tête.

    Compare la première colonne aux marqueurs du flux, insensible à la casse
    après normalisation. Introuvable : rejet, sauf ALLOW_HEADER_FALLBACK.
    """

    markers = {normalize_header(m) for m in spec.header_markers}
    scan = first_column[:max_rows]
    for index, value in enumerate(scan, start=1):
        if normalize_header(value) in markers:
            return index
    if allow_fallback and spec.header_fallback_row is not None:
        return spec.header_fallback_row
    raise StructureError(
        f"En-tête introuvable pour le flux {spec.flow.value} "
        f"(marqueurs={sorted(markers)}, lignes_scannées={min(len(first_column), max_rows)})."
    )


@dataclass(frozen=True)
class BoundColumn:
    spec: ColumnSpec
    source_index: int
    source_header: object
    via_alias: bool = False


@dataclass(frozen=True)
class HeaderBinding:
    header_row: int
    bound: tuple[BoundColumn, ...]
    missing_optional: tuple[ColumnSpec, ...]
    warnings: tuple[str, ...]


def _occurrence_map(headers: list[object]) -> dict[tuple[str, int], int]:
    """(en-tête normalisé, rang) → index 0-based."""

    counts: dict[str, int] = {}
    mapping: dict[tuple[str, int], int] = {}
    for index, raw in enumerate(headers):
        key = normalize_header(raw)
        if key == "":
            continue
        counts[key] = counts.get(key, 0) + 1
        mapping[(key, counts[key])] = index
    return mapping


def bind_columns(headers: list[object], spec: FlowSpec) -> HeaderBinding:
    """Sélectionne les colonnes conservées. Jamais « à peu près »."""

    occurrences = _occurrence_map(headers)
    bound: list[BoundColumn] = []
    missing_optional: list[ColumnSpec] = []
    warnings: list[str] = []

    for column in spec.columns:
        source_index, via_alias, matched_header = _locate(column, headers, occurrences)
        if source_index is None:
            if column.required:
                raise StructureError(
                    f"Colonne requise introuvable: champ={column.field} "
                    f"attendu={column.source_header!r} position={column.position} "
                    f"rang={column.occurrence}."
                )
            missing_optional.append(column)
            warnings.append(
                f"Colonne optionnelle absente: {column.field} "
                f"(attendu {column.source_header!r} pos. {column.position})."
            )
            continue

        found_position = source_index + 1
        found_header = headers[source_index]
        if found_position != column.position:
            raise StructureError(
                f"En-tête inattendu: position={found_position} "
                f"attendu={column.source_header!r} (pos. {column.position}) "
                f"trouvé={found_header!r}."
            )
        bound.append(
            BoundColumn(
                spec=column,
                source_index=source_index,
                source_header=matched_header,
                via_alias=via_alias,
            )
        )

    return HeaderBinding(
        header_row=0,
        bound=tuple(bound),
        missing_optional=tuple(missing_optional),
        warnings=tuple(warnings),
    )


def _locate(
    column: ColumnSpec,
    headers: list[object],
    occurrences: dict[tuple[str, int], int],
) -> tuple[int | None, bool, object]:
    canonical = normalize_header(column.source_header)
    index = occurrences.get((canonical, column.occurrence))
    if index is not None:
        return index, False, headers[index]

    # Alias uniquement si la cible canonique est absente.
    for alias in column.aliases:
        alias_key = normalize_header(alias)
        index = occurrences.get((alias_key, 1))
        if index is not None:
            return index, True, headers[index]
    return None, False, None

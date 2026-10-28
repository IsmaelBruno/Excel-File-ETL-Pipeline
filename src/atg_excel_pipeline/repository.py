"""Tables excel_* et chargement idempotent par nom de fichier."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    delete,
    select,
    text,
)
from sqlalchemy.engine import Engine

from atg_excel_pipeline.schemas import ENTREE_COLUMNS, SORTIE_COLUMNS, FieldType, Flow
from atg_excel_pipeline.transformer import TransformedFile, field_names

ENTREE_TABLE = "excel_entree"
SORTIE_TABLE = "excel_sortie"
REJECT_TABLE = "excel_rejets"
FILES_TABLE = "excel_files"

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


def _sql_type(field_type: FieldType):
    if field_type is FieldType.DATE:
        return Date
    if field_type is FieldType.HEURE:
        return Time
    if field_type is FieldType.NUMERIQUE:
        return Float
    if field_type is FieldType.ENTIER:
        return Integer
    return Text


def _flow_table(metadata: MetaData, flow: Flow) -> Table:
    name = ENTREE_TABLE if flow is Flow.ENTREE else SORTIE_TABLE
    columns = ENTREE_COLUMNS if flow is Flow.ENTREE else SORTIE_COLUMNS
    table_columns = [
        Column("id", Integer, primary_key=True),
        Column("source_name", String(512), nullable=False),
        Column("source_row", Integer, nullable=False),
    ]
    for spec in columns:
        table_columns.append(Column(spec.field, _sql_type(spec.field_type)))
    table_columns.append(
        UniqueConstraint("source_name", "source_row", name=f"uq_{name}_source")
    )
    return Table(name, metadata, *table_columns)


def _reject_table(metadata: MetaData) -> Table:
    return Table(
        REJECT_TABLE,
        metadata,
        Column("id", Integer, primary_key=True),
        Column("source_name", String(512), nullable=False),
        Column("source_row", Integer, nullable=False),
        Column("flow", String(16), nullable=False),
        Column("motif", String(64), nullable=False),
        Column("raw_json", Text),
        UniqueConstraint("source_name", "source_row", "flow", name="uq_excel_rejets"),
    )


def _files_table(metadata: MetaData) -> Table:
    return Table(
        FILES_TABLE,
        metadata,
        Column("id", Integer, primary_key=True),
        Column("source_name", String(512), nullable=False),
        Column("source_path", String(1024), nullable=False),
        Column("flow", String(16), nullable=False),
        Column("file_sha256", String(64), nullable=False),
        Column("status", String(32), nullable=False),
        Column("sheet_name", String(128)),
        Column("header_row", Integer),
        Column("rows_read", Integer, nullable=False, default=0),
        Column("valid_rows", Integer, nullable=False, default=0),
        Column("rejected_rows", Integer, nullable=False, default=0),
        Column("rows_blank_skipped", Integer, nullable=False, default=0),
        Column("cell_errors", Integer, nullable=False, default=0),
        Column("conversion_errors", Integer, nullable=False, default=0),
        Column("duplicate_rows", Integer, nullable=False, default=0),
        Column("date_min", Date),
        Column("date_max", Date),
        Column("error_message", Text),
        Column("processed_at", DateTime(timezone=True), nullable=False),
    )


def metadata_with_tables() -> MetaData:
    metadata = MetaData()
    _flow_table(metadata, Flow.ENTREE)
    _flow_table(metadata, Flow.SORTIE)
    _reject_table(metadata)
    _files_table(metadata)
    return metadata


def ensure_schema(engine: Engine) -> None:
    metadata_with_tables().create_all(engine)


def last_success_hash(engine: Engine, source_name: str, flow: Flow) -> str | None:
    metadata = MetaData()
    files = _files_table(metadata)
    statement = (
        select(files.c.file_sha256)
        .where(
            (files.c.source_name == source_name)
            & (files.c.flow == flow.value)
            & (files.c.status == STATUS_SUCCESS)
        )
        .order_by(files.c.id.desc())
        .limit(1)
    )
    with engine.connect() as connection:
        row = connection.execute(statement).fetchone()
    return None if row is None else str(row[0])


def overlapping_periods(
    engine: Engine,
    flow: Flow,
    source_name: str,
    date_min,
    date_max,
) -> list[str]:
    if date_min is None or date_max is None:
        return []
    metadata = MetaData()
    files = _files_table(metadata)
    statement = (
        select(files.c.source_name)
        .where(
            (files.c.flow == flow.value)
            & (files.c.status == STATUS_SUCCESS)
            & (files.c.source_name != source_name)
            & (files.c.date_min.is_not(None))
            & (files.c.date_max.is_not(None))
            & (files.c.date_min <= date_max)
            & (files.c.date_max >= date_min)
        )
        .distinct()
    )
    with engine.connect() as connection:
        return [str(row[0]) for row in connection.execute(statement)]


def record_failed(
    engine: Engine,
    *,
    source_name: str,
    source_path: Path,
    flow: Flow,
    file_sha256: str,
    error_message: str,
) -> None:
    metadata = MetaData()
    files = _files_table(metadata)
    payload = {
        "source_name": source_name,
        "source_path": str(source_path),
        "flow": flow.value,
        "file_sha256": file_sha256,
        "status": STATUS_FAILED,
        "rows_read": 0,
        "valid_rows": 0,
        "rejected_rows": 0,
        "rows_blank_skipped": 0,
        "cell_errors": 0,
        "conversion_errors": 0,
        "duplicate_rows": 0,
        "error_message": error_message[:4000],
        "processed_at": datetime.now(UTC),
    }
    with engine.begin() as connection:
        connection.execute(files.insert().values(**payload))


def record_skipped(
    engine: Engine,
    *,
    source_name: str,
    source_path: Path,
    flow: Flow,
    file_sha256: str,
) -> None:
    metadata = MetaData()
    files = _files_table(metadata)
    with engine.begin() as connection:
        connection.execute(
            files.insert().values(
                source_name=source_name,
                source_path=str(source_path),
                flow=flow.value,
                file_sha256=file_sha256,
                status=STATUS_SKIPPED,
                rows_read=0,
                valid_rows=0,
                rejected_rows=0,
                rows_blank_skipped=0,
                cell_errors=0,
                conversion_errors=0,
                duplicate_rows=0,
                processed_at=datetime.now(UTC),
            )
        )


def replace_file_payload(
    engine: Engine,
    transformed: TransformedFile,
    *,
    source_path: Path,
    file_sha256: str,
) -> None:
    flow = transformed.parsed.flow
    source_name = transformed.parsed.path.name
    metadata = MetaData()
    data_table = _flow_table(metadata, flow)
    rejects = _reject_table(metadata)
    files = _files_table(metadata)
    quality = transformed.quality
    fields = field_names(flow)

    data_records = []
    for row in transformed.valid_rows:
        record = {"source_name": source_name, "source_row": row["source_row"]}
        for name in fields:
            record[name] = row.get(name)
        data_records.append(record)

    reject_records = [
        {
            "source_name": source_name,
            "source_row": item.source_row,
            "flow": flow.value,
            "motif": item.motif,
            "raw_json": json.dumps(item.raw, default=str, ensure_ascii=False),
        }
        for item in transformed.rejected_rows
    ]

    journal = {
        "source_name": source_name,
        "source_path": str(source_path),
        "flow": flow.value,
        "file_sha256": file_sha256,
        "status": STATUS_SUCCESS,
        "sheet_name": transformed.parsed.sheet_name,
        "header_row": transformed.parsed.header_row,
        "rows_read": quality.rows_read,
        "valid_rows": quality.valid_rows,
        "rejected_rows": quality.rejected_rows,
        "rows_blank_skipped": quality.rows_blank_skipped,
        "cell_errors": quality.cell_errors,
        "conversion_errors": quality.conversion_errors,
        "duplicate_rows": quality.duplicate_rows,
        "date_min": transformed.date_min,
        "date_max": transformed.date_max,
        "error_message": None,
        "processed_at": datetime.now(UTC),
    }

    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:flow), hashtext(:name))"),
                {"flow": flow.value, "name": source_name},
            )
        connection.execute(delete(data_table).where(data_table.c.source_name == source_name))
        connection.execute(
            delete(rejects).where(
                (rejects.c.source_name == source_name) & (rejects.c.flow == flow.value)
            )
        )
        if data_records:
            connection.execute(data_table.insert(), data_records)
        if reject_records:
            connection.execute(rejects.insert(), reject_records)
        connection.execute(files.insert().values(**journal))

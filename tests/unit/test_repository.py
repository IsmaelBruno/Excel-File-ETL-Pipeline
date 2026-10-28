from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, select

from atg_excel_pipeline.parser import ParsedWorkbook
from atg_excel_pipeline.quality import QualityReport
from atg_excel_pipeline.repository import (
    STATUS_SUCCESS,
    ensure_schema,
    last_success_hash,
    metadata_with_tables,
    replace_file_payload,
)
from atg_excel_pipeline.schemas import ENTREE_SPEC, Flow
from atg_excel_pipeline.transformer import TransformedFile


def _transformed(tmp_path: Path, name: str, n_bon: str) -> TransformedFile:
    path = tmp_path / name
    path.write_bytes(b"x")
    parsed = ParsedWorkbook(
        path=path,
        flow=Flow.ENTREE,
        spec=ENTREE_SPEC,
        sheet_name="RDR56REBRE_FR",
        header_row=15,
        source_headers=(),
        rows=(),
        warnings=(),
    )
    row = {
        "source_name": name,
        "source_row": 16,
        "depot_chargeur": "D",
        "produit": "GO",
        "n_bon": n_bon,
        "date_principale": date(2026, 9, 1),
        "ege": 1.0,
    }
    return TransformedFile(
        parsed=parsed,
        valid_rows=[row],
        quality=QualityReport(rows_read=1, valid_rows=1),
        date_min=date(2026, 9, 1),
        date_max=date(2026, 9, 1),
    )


def test_remplace_lignes_du_meme_nom(tmp_path: Path) -> None:
    engine = create_engine("sqlite://")
    ensure_schema(engine)
    first = _transformed(tmp_path, "Entrées Sep-26 JdE.xlsx", "111")
    replace_file_payload(engine, first, source_path=first.parsed.path, file_sha256="a" * 64)
    second = _transformed(tmp_path, "Entrées Sep-26 JdE.xlsx", "222")
    replace_file_payload(engine, second, source_path=second.parsed.path, file_sha256="b" * 64)

    tables = metadata_with_tables()
    entree = tables.tables["excel_entree"]
    with engine.connect() as connection:
        rows = connection.execute(select(entree.c.n_bon)).fetchall()
    assert [r[0] for r in rows] == ["222"]
    assert last_success_hash(engine, "Entrées Sep-26 JdE.xlsx", Flow.ENTREE) == "b" * 64


def test_fichier_nom_different_s_ajoute(tmp_path: Path) -> None:
    engine = create_engine("sqlite://")
    ensure_schema(engine)
    a = _transformed(tmp_path, "Entrées Sep-26 JdE.xlsx", "111")
    b = _transformed(tmp_path, "Entrées Oct-26 JdE.xlsx", "333")
    replace_file_payload(engine, a, source_path=a.parsed.path, file_sha256="a" * 64)
    replace_file_payload(engine, b, source_path=b.parsed.path, file_sha256="c" * 64)
    tables = metadata_with_tables()
    entree = tables.tables["excel_entree"]
    with engine.connect() as connection:
        rows = connection.execute(select(entree.c.source_name, entree.c.n_bon)).fetchall()
    assert len(rows) == 2
    assert STATUS_SUCCESS

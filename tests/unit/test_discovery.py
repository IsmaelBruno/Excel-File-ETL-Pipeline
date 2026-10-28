from __future__ import annotations

from pathlib import Path

from atg_excel_pipeline.discovery import classify_filename, classify_path, iter_source_files
from atg_excel_pipeline.schemas import Flow


def test_classify_entrees_et_passage() -> None:
    assert classify_filename("Entrées Sep-26 JdE.xlsx") is Flow.ENTREE
    assert classify_filename("Passage Sep-26 JdE.xlsx") is Flow.SORTIE
    assert classify_filename("EJE 2026.xlsx") is None
    assert classify_filename("~$Entrées Sep-26 JdE.xlsx") is None


def test_iter_ignore_eje_et_lock(tmp_path: Path) -> None:
    (tmp_path / "Entrées Oct-26 JdE.xlsx").write_bytes(b"PK")
    (tmp_path / "EJE 2026.xlsx").write_bytes(b"PK")
    (tmp_path / "~$Entrées Oct-26 JdE.xlsx").write_bytes(b"PK")
    (tmp_path / "notes.txt").write_text("x")
    found = [p.name for p in iter_source_files(tmp_path, Flow.ENTREE)]
    assert found == ["Entrées Oct-26 JdE.xlsx"]


def test_classify_path_dossier_sortie(tmp_path: Path) -> None:
    dossier = tmp_path / "Sortie"
    dossier.mkdir()
    fichier = dossier / "autre.xlsx"
    fichier.write_bytes(b"PK")
    assert classify_path(fichier) is Flow.SORTIE

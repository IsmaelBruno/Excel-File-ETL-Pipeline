"""Détection des fichiers Entrées*.xlsx et Passage*.xlsx (pas EJE)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from atg_excel_pipeline.schemas import Flow

_EXCEL_SUFFIXES = {".xlsx", ".xlsb"}
_ENTREE_PREFIXES = ("entrées", "entrees", "entrée", "entree")
_SORTIE_PREFIXES = ("passage",)
_SKIP_PREFIXES = ("~$", "eje")


def classify_filename(name: str) -> Flow | None:
    lower = name.lower()
    stem_and_name = lower
    if stem_and_name.startswith(_SKIP_PREFIXES) or Path(name).name.startswith("~$"):
        return None
    stem = Path(name).stem.lower()
    if stem.startswith(_ENTREE_PREFIXES) or lower.startswith(_ENTREE_PREFIXES):
        return Flow.ENTREE
    if stem.startswith(_SORTIE_PREFIXES) or lower.startswith(_SORTIE_PREFIXES):
        return Flow.SORTIE
    return None


def classify_path(path: Path) -> Flow | None:
    if path.name.startswith("~$"):
        return None
    if path.suffix.lower() not in _EXCEL_SUFFIXES:
        return None
    by_name = classify_filename(path.name)
    if by_name is not None:
        return by_name
    parent = path.parent.name.casefold()
    if parent in {"entrée", "entree", "entrées", "entrees"}:
        return Flow.ENTREE
    if parent in {"sortie", "passages"}:
        return Flow.SORTIE
    return None


def iter_source_files(directory: Path, flow: Flow) -> Iterator[Path]:
    if not directory.exists():
        return
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _EXCEL_SUFFIXES:
            continue
        if classify_path(path) is flow:
            yield path

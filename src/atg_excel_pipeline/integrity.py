"""Empreintes de fichiers (copie locale, jamais la source en écriture)."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path, *, chunk_size: int = CHUNK_SIZE) -> str:
    """Retourne le SHA-256 hexadécimal, lu par blocs de 1 Mo."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()

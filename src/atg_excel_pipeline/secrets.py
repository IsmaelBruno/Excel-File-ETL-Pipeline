"""Lecture des secrets : fichier <NOM>_FILE d'abord, variable d'environnement ensuite."""

from __future__ import annotations

import os
from pathlib import Path


def get_secret(name: str, *, required: bool = False) -> str | None:
    """Retourne un secret sans le journaliser.

    ``<NAME>_FILE`` est le point d'intégration préféré. La variable
    d'environnement directe reste un repli pour le développement local.
    """

    file_name = os.getenv(f"{name}_FILE")
    if file_name:
        value = Path(file_name).read_text(encoding="utf-8").strip()
    else:
        value = os.getenv(name)

    if required and not value:
        raise RuntimeError(
            f"Secret manquant: configurez {name}_FILE via votre gestionnaire "
            f"de secrets (repli local: {name})"
        )
    return value or None

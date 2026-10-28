"""Rapport de qualité d'un fichier Excel (sans chargement PostgreSQL)."""

from __future__ import annotations

from dataclasses import dataclass, field

MOTIF_DATE_ABSENTE_OU_INVALIDE = "DATE_ABSENTE_OU_INVALIDE"
MOTIF_DATE_LIVRAISON_ABSENTE_OU_INVALIDE = "DATE_LIVRAISON_ABSENTE_OU_INVALIDE"
MOTIF_PRODUIT_ABSENT = "PRODUIT_ABSENT"


@dataclass
class QualityReport:
    """Compteurs d'un fichier. Les doublons métier n'empêchent pas le chargement."""

    rows_read: int = 0
    rows_blank_skipped: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0
    cell_errors: int = 0
    conversion_errors: int = 0
    duplicate_rows: int = 0
    reject_motifs: dict[str, int] = field(default_factory=dict)

    def add_motif(self, motif: str) -> None:
        self.reject_motifs[motif] = self.reject_motifs.get(motif, 0) + 1

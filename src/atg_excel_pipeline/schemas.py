"""Spécification des colonnes Entrée / Sortie (§8 et §9) sous forme de données."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Flow(str, Enum):
    ENTREE = "entree"
    SORTIE = "sortie"


class FieldType(str, Enum):
    TEXTE = "texte"
    NUMERIQUE = "numerique"
    DATE = "date"
    HEURE = "heure"
    ENTIER = "entier"


@dataclass(frozen=True)
class ColumnSpec:
    """Identité = (en-tête normalisé, rang d'occurrence) + position attendue."""

    position: int
    source_header: str
    field: str
    field_type: FieldType
    occurrence: int = 1
    required: bool = False
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class FlowSpec:
    flow: Flow
    sheet_name: str
    header_markers: tuple[str, ...]
    columns: tuple[ColumnSpec, ...]
    dropped_positions: tuple[int, ...] = ()
    header_fallback_row: int | None = None
    aliases_notes: tuple[str, ...] = field(default_factory=tuple)


ENTREE_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(1, "DépôtChargeur", "depot_chargeur", FieldType.TEXTE),
    ColumnSpec(2, "Produit", "produit", FieldType.TEXTE),
    ColumnSpec(3, "N° Commande ", "n_commande_c3", FieldType.TEXTE, occurrence=1),
    ColumnSpec(4, "N° Bon", "n_bon", FieldType.TEXTE),
    ColumnSpec(5, "N° Commande", "n_commande_c5", FieldType.TEXTE, occurrence=2),
    ColumnSpec(6, "OR/PS", "or_ps", FieldType.TEXTE),
    ColumnSpec(7, "Client", "client", FieldType.TEXTE),
    ColumnSpec(8, "N° Commande réception", "n_commande_reception", FieldType.TEXTE),
    ColumnSpec(9, "Date", "date_principale", FieldType.DATE, required=True, occurrence=1),
    ColumnSpec(10, "Type", "type", FieldType.TEXTE),
    ColumnSpec(11, "N°", "n_c11", FieldType.TEXTE, occurrence=1),
    ColumnSpec(12, "Transporteur", "transporteur", FieldType.TEXTE),
    ColumnSpec(13, "Volume recu", "ege", FieldType.NUMERIQUE),
    ColumnSpec(14, "Volume Standard", "volume_standard", FieldType.NUMERIQUE),
    ColumnSpec(15, "Volume Amb", "volume_amb_c15", FieldType.NUMERIQUE, occurrence=1),
    ColumnSpec(16, "Volume Std", "volume_std_c16", FieldType.NUMERIQUE, occurrence=1),
    ColumnSpec(17, "Volume Amb", "volume_amb_c17", FieldType.NUMERIQUE, occurrence=2),
    ColumnSpec(18, "Volume Std", "volume_std_c18", FieldType.NUMERIQUE, occurrence=2),
    ColumnSpec(20, "A1", "a1", FieldType.TEXTE),
    ColumnSpec(21, "A2", "a2", FieldType.TEXTE),
    ColumnSpec(22, "DEP", "dep", FieldType.TEXTE, aliases=("A3",)),
    ColumnSpec(23, "DIST", "dist", FieldType.TEXTE, aliases=("A4",)),
    ColumnSpec(27, "Perte Déch", "perte_dech", FieldType.NUMERIQUE),
    ColumnSpec(30, "Date", "date_c30", FieldType.DATE, occurrence=2),
    ColumnSpec(31, "N°", "heure", FieldType.HEURE, occurrence=2),
)

ENTREE_DROPPED = (
    19,
    24,
    25,
    26,
    28,
    29,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
)

SORTIE_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(1, "DépôtLivrancier", "depot_livrancier", FieldType.TEXTE),
    ColumnSpec(2, "Produit", "produit", FieldType.TEXTE, required=True, occurrence=1),
    ColumnSpec(3, "N° CF Client", "n_cf_client", FieldType.TEXTE),
    ColumnSpec(4, "Client", "client", FieldType.TEXTE, occurrence=1),
    ColumnSpec(5, "N° BSL", "n_bsl", FieldType.ENTIER),
    ColumnSpec(6, "N° Commande JDE", "n_commande_jde", FieldType.TEXTE),
    ColumnSpec(7, "Date Livraison", "date_livraison", FieldType.DATE, required=True),
    ColumnSpec(8, "Type", "type", FieldType.TEXTE),
    ColumnSpec(9, "N°Véhicule", "n_vehicule", FieldType.TEXTE),
    ColumnSpec(10, "Transporteur", "transporteur", FieldType.TEXTE),
    ColumnSpec(11, "VolumeAmb", "volume_amb", FieldType.NUMERIQUE),
    ColumnSpec(13, "Volume Standard", "egs", FieldType.NUMERIQUE),
    ColumnSpec(15, "N° Bac de livraison", "n_bac_livraison", FieldType.TEXTE),
    ColumnSpec(16, "T°", "temperature", FieldType.NUMERIQUE),
    ColumnSpec(17, "Densité à 15", "densite_15", FieldType.NUMERIQUE),
    ColumnSpec(18, "City", "city", FieldType.TEXTE),
    ColumnSpec(19, "A1", "a1", FieldType.TEXTE),
    ColumnSpec(20, "SITE Chargeur", "site_chargeur", FieldType.TEXTE),
    ColumnSpec(21, "CLIENT", "client_c21", FieldType.TEXTE, occurrence=2),
    ColumnSpec(22, "SITE Dest", "site_dest", FieldType.TEXTE),
    ColumnSpec(25, "TCDE", "tcde", FieldType.TEXTE),
    ColumnSpec(27, "COMM", "comm", FieldType.ENTIER),
    ColumnSpec(29, "N° OT", "n_ot", FieldType.ENTIER),
    ColumnSpec(30, "HHMMSS", "heure", FieldType.HEURE),
)

SORTIE_DROPPED = (12, 14, 23, 24, 26, 28, 31, 32, 33, 34, 35, 36, 37, 38)

ENTREE_SPEC = FlowSpec(
    flow=Flow.ENTREE,
    sheet_name="RDR56REBRE_FR",
    header_markers=("DépôtChargeur", "Dépôt Chargeur", "Dépôt chargeur"),
    columns=ENTREE_COLUMNS,
    dropped_positions=ENTREE_DROPPED,
    header_fallback_row=14,
)

SORTIE_SPEC = FlowSpec(
    flow=Flow.SORTIE,
    sheet_name="RDR56REBSL_FR",
    header_markers=("DépôtLivrancier", "Dépôt Livrancier"),
    columns=SORTIE_COLUMNS,
    dropped_positions=SORTIE_DROPPED,
    header_fallback_row=13,
)

SPECS: dict[Flow, FlowSpec] = {
    Flow.ENTREE: ENTREE_SPEC,
    Flow.SORTIE: SORTIE_SPEC,
}


def spec_for(flow: Flow | str) -> FlowSpec:
    if isinstance(flow, str):
        flow = Flow(flow)
    return SPECS[flow]

from __future__ import annotations

import pytest

from atg_excel_pipeline.headers import (
    StructureError,
    bind_columns,
    find_header_row,
    normalize_header,
)
from atg_excel_pipeline.schemas import ENTREE_SPEC, SORTIE_SPEC


def test_normalize_header_nfkc_espaces_casse_et_sauts() -> None:
    assert normalize_header("Dépôt Chargeur") == "dépôtchargeur"
    assert normalize_header("DépôtChargeur") == "dépôtchargeur"
    assert normalize_header("Dépôt\nChargeur") == "dépôtchargeur"
    assert normalize_header("Dépôt\xa0Chargeur") == "dépôtchargeur"
    assert normalize_header("CLIENT") == normalize_header("Client") == "client"
    assert normalize_header("N° Commande ") == normalize_header("N° Commande")
    assert normalize_header("Vol amb\nchargé") == "volambchargé"


def test_find_header_row_entree_ligne_15() -> None:
    col_a: list[object] = [None] * 14 + ["DépôtChargeur"]
    assert find_header_row(col_a, ENTREE_SPEC, max_rows=200) == 15


def test_find_header_row_alias_depot_chargeur() -> None:
    col_a: list[object] = [None] * 13 + ["Dépôt Chargeur"]
    assert find_header_row(col_a, ENTREE_SPEC) == 14


def test_find_header_row_introuvable_sans_repli() -> None:
    with pytest.raises(StructureError, match="En-tête introuvable"):
        find_header_row(["présentation"], ENTREE_SPEC, max_rows=10, allow_fallback=False)


def test_find_header_row_repli_optionnel() -> None:
    assert (
        find_header_row(["x"] * 20, ENTREE_SPEC, allow_fallback=True) == ENTREE_SPEC.header_fallback_row
    )


ENTREE_SEP26 = [
    "DépôtChargeur",
    "Produit",
    "N° Commande ",
    "N° Bon",
    "N° Commande",
    "OR/PS",
    "Client",
    "N° Commande réception",
    "Date",
    "Type",
    "N°",
    "Transporteur",
    "Volume recu",
    "Volume Standard",
    "Volume Amb",
    "Volume Std",
    "Volume Amb",
    "Volume Std",
    "Volume chargé Ajusté",
    "A1",
    "A2",
    "DEP",
    "DIST",
    "P. Transp",
    "P. Recep",
    "A7",
    "Perte Déch",
    "Perte TRANS",
    "Date OT",
    "Date",
    "N°",
    "Nom du",
    "Dépôt",
    "Date",
    "Distributeur",
    "Bon",
    "Réf",
    "Produit",
    "Vol amb\nchargé",
    "Vol 15\nchargé",
    "Vol amb \nArrivée",
    "Vol 15\nArrivée",
    "Vol amb\ndépart",
    "JOUR_OT",
    "Bac-S Via N° OT",
    "Date entrée",
    "Bac-R",
]


def test_bind_entree_sep26_identites_et_rangs() -> None:
    binding = bind_columns(ENTREE_SEP26, ENTREE_SPEC)
    by_field = {b.spec.field: b for b in binding.bound}
    assert by_field["date_principale"].source_index == 8
    assert by_field["date_c30"].source_index == 29
    assert by_field["n_commande_c3"].source_index == 2
    assert by_field["n_commande_c5"].source_index == 4
    assert by_field["volume_amb_c15"].source_index == 14
    assert by_field["volume_amb_c17"].source_index == 16
    assert by_field["heure"].source_index == 30
    assert "date_principale" not in {c.field for c in binding.missing_optional}
    # Date rang 3 (pos. 34) ignorée volontairement
    assert 34 not in {b.spec.position for b in binding.bound}


def test_bind_entree_alias_a3_a4_si_dep_absent() -> None:
    headers = list(ENTREE_SEP26)
    headers[21] = "A3"
    headers[22] = "A4"
    binding = bind_columns(headers, ENTREE_SPEC)
    by_field = {b.spec.field: b for b in binding.bound}
    assert by_field["dep"].via_alias is True
    assert by_field["dist"].via_alias is True
    assert by_field["dep"].source_index == 21


def test_bind_position_inattendue() -> None:
    headers = list(ENTREE_SEP26)
    headers[8], headers[9] = headers[9], headers[8]
    with pytest.raises(StructureError, match="En-tête inattendu"):
        bind_columns(headers, ENTREE_SPEC)


def test_bind_colonne_requise_absente() -> None:
    headers = list(ENTREE_SEP26)
    headers[8] = "PasUneDate"
    headers[29] = "SansDate"
    headers[33] = "ToujoursPas"
    with pytest.raises(StructureError, match="Colonne requise introuvable"):
        bind_columns(headers, ENTREE_SPEC)


def test_bind_colonne_optionnelle_absente() -> None:
    headers = list(ENTREE_SEP26)
    headers[5] = None
    binding = bind_columns(headers, ENTREE_SPEC)
    assert any(c.field == "or_ps" for c in binding.missing_optional)
    assert any("or_ps" in w for w in binding.warnings)


SORTIE_SEP26 = [
    "DépôtLivrancier",
    "Produit",
    "N° CF Client",
    "Client",
    "N° BSL",
    "N° Commande JDE",
    "Date Livraison",
    "Type",
    "N°Véhicule",
    "Transporteur",
    "VolumeAmb",
    "UM",
    "Volume Standard",
    "UM",
    "N° Bac de livraison",
    "T°",
    "Densité à 15",
    "City",
    "A1",
    "SITE Chargeur",
    "CLIENT",
    "SITE Dest",
    "VS",
    "A2",
    "TCDE",
    "CRED",
    "COMM",
    "Date OT",
    "N° OT",
    "HHMMSS",
    "Dépôt réceptionnaire",
    "Distributeur",
    "Date chargement",
    "Bon BST",
    "Réf",
    "Produit",
    "Vol amb chargé",
    "Vol 15 chargé",
    None,
]


def test_bind_sortie_client_vs_client_c21() -> None:
    binding = bind_columns(SORTIE_SEP26, SORTIE_SPEC)
    by_field = {b.spec.field: b for b in binding.bound}
    assert by_field["client"].source_index == 3
    assert by_field["client_c21"].source_index == 20
    assert by_field["egs"].source_index == 12
    assert by_field["produit"].source_index == 1
    assert 36 not in {b.spec.position for b in binding.bound}


def test_find_header_row_sortie() -> None:
    col_a: list[object] = [None] * 13 + ["DépôtLivrancier"]
    assert find_header_row(col_a, SORTIE_SPEC) == 14

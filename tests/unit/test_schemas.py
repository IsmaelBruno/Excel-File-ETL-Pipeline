from __future__ import annotations

from atg_excel_pipeline.headers import normalize_header
from atg_excel_pipeline.schemas import ENTREE_COLUMNS, SORTIE_COLUMNS, FieldType


def test_entree_date_requise_unique() -> None:
    required = [c for c in ENTREE_COLUMNS if c.required]
    assert [c.field for c in required] == ["date_principale"]
    assert required[0].field_type is FieldType.DATE


def test_sortie_champs_requis() -> None:
    required = {c.field for c in SORTIE_COLUMNS if c.required}
    assert required == {"produit", "date_livraison"}


def test_suffixes_position_colonnes_ambigues() -> None:
    fields = {c.field: c.position for c in ENTREE_COLUMNS}
    assert fields["n_commande_c3"] == 3
    assert fields["n_commande_c5"] == 5
    assert fields["volume_amb_c15"] == 15
    assert fields["volume_std_c18"] == 18
    assert fields["date_c30"] == 30


def test_client_sortie_meme_normalisation_rangs_distincts() -> None:
    client = next(c for c in SORTIE_COLUMNS if c.field == "client")
    client_c21 = next(c for c in SORTIE_COLUMNS if c.field == "client_c21")
    assert normalize_header(client.source_header) == normalize_header(client_c21.source_header)
    assert client.occurrence == 1
    assert client_c21.occurrence == 2
    assert client.position == 4
    assert client_c21.position == 21

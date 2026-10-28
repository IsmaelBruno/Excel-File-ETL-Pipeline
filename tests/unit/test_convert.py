from __future__ import annotations

from datetime import date, time

from atg_excel_pipeline.convert import (
    clean_text,
    parse_date,
    parse_integer,
    parse_number,
    parse_time_entree,
    parse_time_sortie,
)


def test_nombre_espace_et_virgule() -> None:
    assert parse_number("1 234,5").value == 1234.5
    assert parse_number(12.5).value == 12.5


def test_nombre_milliers_point_non_gere() -> None:
    result = parse_number("1.234,5")
    assert result.value is None
    assert result.error == "conversion"


def test_erreur_excel() -> None:
    assert parse_number("#N/A").error == "cell"
    assert parse_date("#VALEUR!").error == "cell"


def test_booleen_refuse_en_nombre() -> None:
    assert parse_number(True).error == "conversion"


def test_texte_identifiant_sans_point_zero() -> None:
    assert clean_text(12345.0) == "12345"
    assert clean_text(12345) == "12345"


def test_heure_sortie_hhmmss() -> None:
    assert parse_time_sortie(93005).value == time(9, 30, 5)
    assert parse_time_sortie(143015.0).value == time(14, 30, 15)
    assert parse_time_sortie("abc").error == "conversion"


def test_heure_entree_time_et_fraction() -> None:
    assert parse_time_entree(time(12, 0, 47)).value == time(12, 0, 47)
    assert parse_time_entree(0.5).value == time(12, 0, 0)
    assert parse_time_entree("08:17:17").value == time(8, 17, 17)


def test_date_texte_jour_premier() -> None:
    assert parse_date("01/09/2026").value == date(2026, 9, 1)
    assert parse_date("2026-09-01").value == date(2026, 9, 1)


def test_entier_half_even() -> None:
    assert parse_integer(1.5).value == 2
    assert parse_integer(2.5).value == 2

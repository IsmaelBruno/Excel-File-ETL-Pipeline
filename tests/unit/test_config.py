from __future__ import annotations

from atg_excel_pipeline.config import Settings, load_settings


def test_from_environ_sans_lire_os(tmp_path) -> None:
    env = {
        "ENTREE_DIR": str(tmp_path / "in"),
        "SORTIE_DIR": str(tmp_path / "out"),
        "HEADER_SCAN_MAX_ROWS": "50",
        "ALLOW_HEADER_FALLBACK": "true",
        "DB_HOST": "example.invalid",
        "DB_PASSWORD": "ne-doit-pas-etre-stocke",
    }
    settings = Settings.from_environ(env)
    assert settings.entree_dir == tmp_path / "in"
    assert settings.header_scan_max_rows == 50
    assert settings.allow_header_fallback is True
    assert settings.allow_first_sheet_fallback is False
    assert settings.date_dayfirst is True
    assert "ne-doit-pas-etre-stocke" not in settings.__dict__.values()
    assert not hasattr(settings, "db_password") or callable(getattr(settings, "db_password"))


def test_load_settings_avec_mapping_ignore_dotenv() -> None:
    settings = load_settings(environ={"ENTREE_DIR": r"D:\fake\Entrée", "SORTIE_DIR": r"D:\fake\Sortie"})
    assert str(settings.entree_dir) == r"D:\fake\Entrée"

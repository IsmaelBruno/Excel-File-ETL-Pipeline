"""Configuration : objet Settings instancié explicitement, pas de lecture à l'import."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from atg_excel_pipeline.secrets import get_secret

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "oui", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    return int(value)


def _as_path(value: str | None, default: Path) -> Path:
    if not value:
        path = default
    else:
        path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


@dataclass(frozen=True)
class Settings:
    entree_dir: Path
    sortie_dir: Path
    staging_dir: Path
    rejected_dir: Path
    log_dir: Path
    log_level: str
    header_scan_max_rows: int
    allow_header_fallback: bool
    allow_first_sheet_fallback: bool
    date_dayfirst: bool
    scan_interval_seconds: int
    watch_use_polling: bool
    stability_required_checks: int
    stability_check_seconds: float
    max_attempts: int
    retry_backoff_seconds: float
    db_host: str | None
    db_port: int
    db_name: str | None
    db_user: str | None
    db_sslmode: str
    db_pool_size: int
    db_max_overflow: int

    @classmethod
    def from_environ(cls, environ: dict[str, str] | None = None) -> Settings:
        """Construit les réglages à partir d'un mapping (défaut: os.environ)."""

        env = environ if environ is not None else os.environ
        return cls(
            entree_dir=_as_path(env.get("ENTREE_DIR"), Path("data/entree")),
            sortie_dir=_as_path(env.get("SORTIE_DIR"), Path("data/sortie")),
            staging_dir=_as_path(env.get("STAGING_DIR"), PROJECT_ROOT / "data" / "staging"),
            rejected_dir=_as_path(env.get("REJECTED_DIR"), PROJECT_ROOT / "data" / "rejected"),
            log_dir=_as_path(env.get("LOG_DIR"), PROJECT_ROOT / "logs"),
            log_level=(env.get("LOG_LEVEL") or "INFO").upper(),
            header_scan_max_rows=_as_int(env.get("HEADER_SCAN_MAX_ROWS"), 200),
            allow_header_fallback=_as_bool(env.get("ALLOW_HEADER_FALLBACK"), False),
            allow_first_sheet_fallback=_as_bool(env.get("ALLOW_FIRST_SHEET_FALLBACK"), False),
            date_dayfirst=_as_bool(env.get("DATE_DAYFIRST"), True),
            scan_interval_seconds=_as_int(env.get("SCAN_INTERVAL_SECONDS"), 60),
            watch_use_polling=_as_bool(env.get("WATCH_USE_POLLING"), False),
            stability_required_checks=_as_int(env.get("STABILITY_REQUIRED_CHECKS"), 3),
            stability_check_seconds=float(env.get("STABILITY_CHECK_SECONDS") or 2),
            max_attempts=_as_int(env.get("MAX_ATTEMPTS"), 5),
            retry_backoff_seconds=float(env.get("RETRY_BACKOFF_SECONDS") or 5),
            db_host=env.get("DB_HOST") or None,
            db_port=_as_int(env.get("DB_PORT"), 5432),
            db_name=env.get("DB_NAME") or None,
            db_user=env.get("DB_USER") or None,
            db_sslmode=env.get("DB_SSLMODE") or "prefer",
            db_pool_size=_as_int(env.get("DB_POOL_SIZE"), 5),
            db_max_overflow=_as_int(env.get("DB_MAX_OVERFLOW"), 10),
        )

    def db_password(self) -> str | None:
        """Mot de passe lu à la demande, jamais stocké sur l'instance Settings."""

        return get_secret("DB_PASSWORD")


def load_settings(*, dotenv_path: Path | None = None, environ: dict[str, str] | None = None) -> Settings:
    """Charge éventuellement un .env puis instancie Settings.

    ``environ`` fourni (tests) : le fichier .env n'est pas lu.
    """

    if environ is None:
        path = dotenv_path if dotenv_path is not None else PROJECT_ROOT / ".env"
        load_dotenv(path)
    return Settings.from_environ(environ)

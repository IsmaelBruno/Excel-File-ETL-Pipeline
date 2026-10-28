"""Point d'entrée CLI : check, init-db, scan-once, process. Pas de surveillance."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from atg_excel_pipeline import __version__
from atg_excel_pipeline.config import load_settings
from atg_excel_pipeline.logging_config import configure_logging
from atg_excel_pipeline.schemas import Flow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atg-excel-pipeline",
        description="ETL Excel JDE Entrées/Passage vers PostgreSQL.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="Vérifie la configuration (aucun secret affiché).")
    sub.add_parser("init-db", help="Crée les tables atg_excel_* si absentes.")
    sub.add_parser("scan-once", help="Parcourt Entrée/Sortie et charge PostgreSQL.")
    process = sub.add_parser("process", help="Traite un fichier puis charge PostgreSQL.")
    process.add_argument("fichier")
    process.add_argument("--flow", choices=("entree", "sortie"))
    sub.add_parser("run", help="Surveillance continue (hors périmètre ETL).")
    return parser


def cmd_check() -> int:
    settings = load_settings()
    print(f"ENTREE_DIR={settings.entree_dir} existe={settings.entree_dir.exists()}")
    print(f"SORTIE_DIR={settings.sortie_dir} existe={settings.sortie_dir.exists()}")
    print(f"STAGING_DIR={settings.staging_dir}")
    print(f"HEADER_SCAN_MAX_ROWS={settings.header_scan_max_rows}")
    print(f"ALLOW_HEADER_FALLBACK={settings.allow_header_fallback}")
    print(f"ALLOW_FIRST_SHEET_FALLBACK={settings.allow_first_sheet_fallback}")
    print(f"DB_HOST={'défini' if settings.db_host else 'absent'}")
    print(f"DB_PORT={settings.db_port}")
    print(f"DB_NAME={'défini' if settings.db_name else 'absent'}")
    print(f"DB_USER={'défini' if settings.db_user else 'absent'}")
    print("DB_PASSWORD=*** (jamais affiché)")
    missing = settings.missing_db_keys()
    if missing:
        print("Connexion DB: configuration incomplète (" + ", ".join(missing) + ")")
        return 0
    from sqlalchemy import text

    from atg_excel_pipeline.database import create_database_engine

    engine = create_database_engine(settings)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    print("Connexion DB: OK")
    engine.dispose()
    return 0


def _engine_and_log():
    settings = load_settings()
    configure_logging(settings)
    from atg_excel_pipeline.database import create_database_engine
    from atg_excel_pipeline.repository import ensure_schema

    engine = create_database_engine(settings)
    ensure_schema(engine)
    return settings, engine


def cmd_init_db() -> int:
    settings, engine = _engine_and_log()
    print("Tables atg_excel_* prêtes.")
    engine.dispose()
    return 0


def cmd_scan_once() -> int:
    from atg_excel_pipeline.pipeline import scan_once

    settings, engine = _engine_and_log()
    results = scan_once(settings, engine)
    engine.dispose()
    _print_results(results)
    if any(item.status == "failed" for item in results):
        return 1
    return 0


def cmd_process(fichier: str, flow_name: str | None) -> int:
    from atg_excel_pipeline.pipeline import process_file

    settings, engine = _engine_and_log()
    flow = Flow(flow_name) if flow_name else None
    result = process_file(Path(fichier), settings, engine, flow=flow)
    engine.dispose()
    _print_results([result])
    return 0 if result.status in {"success", "skipped"} else 1


def _print_results(results) -> None:
    if not results:
        print("Aucun fichier Entrées*/Passage* trouvé.")
        return
    for item in results:
        extra = ""
        if item.status == "success":
            extra = f" valides={item.valid_rows} rejets={item.rejected_rows}"
        line = f"{item.status:8} {item.flow.value:7} {item.path.name}{extra} {item.message}"
        print(line.rstrip())


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check()
    if args.command == "init-db":
        return cmd_init_db()
    if args.command == "scan-once":
        return cmd_scan_once()
    if args.command == "process":
        return cmd_process(args.fichier, args.flow)
    if args.command == "run":
        print(
            "La surveillance continue n'est pas dans le périmètre ETL. "
            "Utilisez scan-once (la copie L: → D:\\SBM\\BI_SBM est un autre script).",
            file=sys.stderr,
        )
        return 2
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

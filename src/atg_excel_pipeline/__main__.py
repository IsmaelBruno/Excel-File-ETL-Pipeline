"""Point d'entrée CLI. Commandes hors échafaudage : non implémentées à cette étape."""

from __future__ import annotations

import argparse
import sys

from atg_excel_pipeline import __version__
from atg_excel_pipeline.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atg-excel-pipeline",
        description="Pipeline Excel JDE Entrée/Sortie vers PostgreSQL.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="Vérifie la configuration (aucun secret affiché).")
    sub.add_parser("init-db", help="Crée les tables atg_excel_* (non implémenté).")
    sub.add_parser("run", help="Surveillance continue (non implémenté).")
    sub.add_parser("scan-once", help="Un passage (non implémenté).")
    process = sub.add_parser("process", help="Traite un fichier (non implémenté).")
    process.add_argument("fichier")
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
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return cmd_check()
    if args.command is None:
        parser.print_help()
        return 0
    print(f"Commande {args.command!r} non implémentée (étape échafaudage).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

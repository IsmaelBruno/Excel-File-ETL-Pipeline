"""Orchestration ETL : extraire → transformer → charger (sans surveillance)."""

from __future__ import annotations

import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.engine import Engine

from atg_excel_pipeline.config import Settings
from atg_excel_pipeline.discovery import classify_path, iter_source_files
from atg_excel_pipeline.headers import StructureError
from atg_excel_pipeline.integrity import sha256_file
from atg_excel_pipeline.logging_config import LOGGER_NAME
from atg_excel_pipeline.parser import parse_workbook
from atg_excel_pipeline.repository import (
    last_success_hash,
    overlapping_periods,
    record_failed,
    replace_file_payload,
)
from atg_excel_pipeline.schemas import Flow
from atg_excel_pipeline.transformer import transform_workbook

logger = logging.getLogger(LOGGER_NAME)


@dataclass
class FileResult:
    path: Path
    flow: Flow
    status: str
    message: str = ""
    valid_rows: int = 0
    rejected_rows: int = 0


def copy_to_staging(source: Path, settings: Settings, flow: Flow) -> Path:
    dest_dir = settings.staging_dir / flow.value
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / source.name
    part = dest.with_name(dest.name + ".part")
    last_error: Exception | None = None
    for attempt in range(1, settings.max_attempts + 1):
        try:
            shutil.copy2(source, part)
            if dest.exists():
                dest.unlink()
            part.replace(dest)
            return dest
        except OSError as exc:
            last_error = exc
            logger.warning(
                "Copie impossible (%s/%s) %s: %s",
                attempt,
                settings.max_attempts,
                source.name,
                exc,
            )
            time.sleep(settings.retry_backoff_seconds * attempt)
    raise RuntimeError(f"Copie staging échouée: {source}") from last_error


def process_file(
    source: Path,
    settings: Settings,
    engine: Engine,
    *,
    flow: Flow | None = None,
) -> FileResult:
    resolved = flow or classify_path(source)
    if resolved is None:
        return FileResult(source, Flow.ENTREE, "ignored", "Nom hors Entrées*/Passage*")

    try:
        staged = copy_to_staging(source, settings, resolved)
        digest = sha256_file(staged)
    except Exception as exc:
        logger.exception("Préparation impossible pour %s", source.name)
        return FileResult(source, resolved, "failed", str(exc))

    previous = last_success_hash(engine, source.name, resolved)
    if previous == digest:
        logger.info("Déjà chargé (même SHA-256): %s", source.name)
        return FileResult(source, resolved, "skipped", "hash identique")

    try:
        parsed = parse_workbook(staged, resolved, settings)
        transformed = transform_workbook(parsed, settings)
    except StructureError as exc:
        logger.error("Structure rejetée %s: %s", source.name, exc)
        record_failed(
            engine,
            source_name=source.name,
            source_path=source,
            flow=resolved,
            file_sha256=digest,
            error_message=str(exc),
        )
        return FileResult(source, resolved, "failed", str(exc))
    except Exception as exc:
        logger.exception("Lecture/transformation %s", source.name)
        record_failed(
            engine,
            source_name=source.name,
            source_path=source,
            flow=resolved,
            file_sha256=digest,
            error_message=str(exc),
        )
        return FileResult(source, resolved, "failed", str(exc))

    overlaps = overlapping_periods(
        engine, resolved, source.name, transformed.date_min, transformed.date_max
    )
    if overlaps:
        logger.warning(
            "Chevauchement de périodes %s (%s → %s) avec %s",
            source.name,
            transformed.date_min,
            transformed.date_max,
            ", ".join(overlaps),
        )

    try:
        replace_file_payload(engine, transformed, source_path=source, file_sha256=digest)
    except Exception as exc:
        logger.exception("Chargement PostgreSQL %s", source.name)
        record_failed(
            engine,
            source_name=source.name,
            source_path=source,
            flow=resolved,
            file_sha256=digest,
            error_message=str(exc),
        )
        return FileResult(source, resolved, "failed", str(exc))

    logger.info(
        "Chargé %s flow=%s valides=%s rejets=%s vides=%s",
        source.name,
        resolved.value,
        transformed.quality.valid_rows,
        transformed.quality.rejected_rows,
        transformed.quality.rows_blank_skipped,
    )
    return FileResult(
        source,
        resolved,
        "success",
        valid_rows=transformed.quality.valid_rows,
        rejected_rows=transformed.quality.rejected_rows,
    )


def scan_once(settings: Settings, engine: Engine) -> list[FileResult]:
    results: list[FileResult] = []
    for flow, directory in (
        (Flow.ENTREE, settings.entree_dir),
        (Flow.SORTIE, settings.sortie_dir),
    ):
        for path in iter_source_files(directory, flow):
            results.append(process_file(path, settings, engine, flow=flow))
    return results

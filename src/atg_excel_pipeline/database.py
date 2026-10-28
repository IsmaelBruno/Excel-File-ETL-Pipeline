"""Moteur SQLAlchemy PostgreSQL (psycopg3), secrets jamais journalisés."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine

from atg_excel_pipeline.config import Settings


def create_database_engine(settings: Settings, *, echo: bool = False) -> Engine:
    missing = settings.missing_db_keys()
    if missing:
        raise RuntimeError("Configuration PostgreSQL manquante: " + ", ".join(missing))

    url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        query={"sslmode": settings.db_sslmode},
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=echo,
    )

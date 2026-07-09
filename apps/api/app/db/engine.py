"""Async SQLAlchemy engine.

The engine is created lazily so that importing this module (e.g. from tests or
Alembic) does not open connections. Pool sizing is conservative: Neon pools
upstream, and the API runs 4 Gunicorn workers on a 4 vCPU host.
"""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Return the process-wide async engine (created on first use)."""
    return create_async_engine(
        str(settings.database_url),
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,
    )

"""Health check endpoints.

- GET /health         — instant liveness: version + uptime, never touches the DB
- GET /health/deep    — dependency check (Postgres, Redis, Celery), static-key protected
- GET /health/version — git commit hash + deployment timestamp for deploy verification
"""

import asyncio
import logging
import secrets
import time
from collections.abc import Coroutine
from typing import Annotated, Literal

import redis.asyncio as aioredis
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.db.base import get_engine
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

_STARTED_AT = time.monotonic()

# Each dependency check gets its own budget; a hung dependency must degrade
# the report, never 500 the endpoint (the deploy pipeline depends on it).
PER_CHECK_TIMEOUT_S = 3.0


class HealthResponse(BaseModel):
    """Instant liveness payload."""

    status: Literal["ok"]
    version: str
    commit: str
    uptime_seconds: float


class DependencyStatus(BaseModel):
    """Status of one downstream dependency."""

    healthy: bool
    detail: str


class DeepHealthResponse(BaseModel):
    """Full dependency report; overall status degrades if any check fails."""

    status: Literal["ok", "degraded"]
    database: DependencyStatus
    redis: DependencyStatus
    celery: DependencyStatus


class VersionResponse(BaseModel):
    """Deployment identity used by deploy.yml to verify the new release."""

    commit: str
    deployed_at: str
    version: str


@router.get(
    "/health",
    summary="Liveness probe",
    description=(
        "Returns immediately with the app version and uptime. Never touches the "
        "database or any dependency — must respond within 50ms. Polled by Uptime "
        "Robot every 5 minutes."
    ),
    response_model=HealthResponse,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "version": "1.0.0",
                        "commit": "a1b2c3d",
                        "uptime_seconds": 12345.6,
                    }
                }
            }
        }
    },
)
async def health() -> HealthResponse:
    """Instant liveness — no I/O of any kind."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        commit=settings.git_commit_sha,
        uptime_seconds=round(time.monotonic() - _STARTED_AT, 1),
    )


async def _check_database() -> DependencyStatus:
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return DependencyStatus(healthy=True, detail="connected")
    except Exception as exc:  # noqa: BLE001 — any failure means unhealthy
        return DependencyStatus(healthy=False, detail=type(exc).__name__)


async def _check_redis() -> DependencyStatus:
    client: aioredis.Redis = aioredis.from_url(str(settings.redis_url))  # type: ignore[no-untyped-call]
    try:
        await client.ping()
        return DependencyStatus(healthy=True, detail="connected")
    except Exception as exc:  # noqa: BLE001
        return DependencyStatus(healthy=False, detail=type(exc).__name__)
    finally:
        await client.aclose()


async def _check_celery() -> DependencyStatus:
    def _ping() -> int:
        # Explicit non-retrying connection: kombu's default retry policy would
        # block for minutes against a dead broker.
        with celery_app.connection(connect_timeout=2, transport_options={"max_retries": 1}) as conn:
            replies = celery_app.control.ping(timeout=2.0, connection=conn)
        return len(replies or [])

    try:
        worker_count = await asyncio.to_thread(_ping)
    except Exception as exc:  # noqa: BLE001
        return DependencyStatus(healthy=False, detail=type(exc).__name__)
    if worker_count == 0:
        return DependencyStatus(healthy=False, detail="0 workers responding")
    return DependencyStatus(healthy=True, detail=f"{worker_count} worker(s)")


async def _bounded(check: Coroutine[None, None, DependencyStatus]) -> DependencyStatus:
    """Apply the per-check budget; a timeout is a degraded status, not a 500."""
    try:
        return await asyncio.wait_for(check, timeout=PER_CHECK_TIMEOUT_S)
    except TimeoutError:
        return DependencyStatus(healthy=False, detail=f"timeout after {PER_CHECK_TIMEOUT_S:.0f}s")


@router.get(
    "/health/deep",
    summary="Deep dependency check",
    description=(
        "Checks PostgreSQL, Redis, and Celery worker availability. Protected by a "
        "static API key (X-Health-Key header) because the deployment pipeline calls "
        "it before any JWT infrastructure is available."
    ),
    response_model=DeepHealthResponse,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "database": {"healthy": True, "detail": "connected"},
                        "redis": {"healthy": True, "detail": "connected"},
                        "celery": {"healthy": True, "detail": "8 worker(s)"},
                    }
                }
            }
        },
        401: {"description": "Missing or invalid X-Health-Key"},
    },
)
async def health_deep(
    x_health_key: Annotated[str, Header(alias="X-Health-Key")] = "",
) -> DeepHealthResponse:
    """Dependency check for the deploy pipeline and on-call diagnosis."""
    if not secrets.compare_digest(x_health_key, settings.health_api_key):
        logger.warning("health/deep called with invalid key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_health_key",
                "message": "X-Health-Key header missing or incorrect",
                "details": {},
            },
        )
    db, redis_status, celery_status = await asyncio.gather(
        _bounded(_check_database()),
        _bounded(_check_redis()),
        _bounded(_check_celery()),
    )
    all_healthy = db.healthy and redis_status.healthy and celery_status.healthy
    return DeepHealthResponse(
        status="ok" if all_healthy else "degraded",
        database=db,
        redis=redis_status,
        celery=celery_status,
    )


@router.get(
    "/health/version",
    summary="Deployment version",
    description=(
        "Returns the git commit hash and deployment timestamp. deploy.yml compares "
        "this against the pushed commit to confirm the new release is live."
    ),
    response_model=VersionResponse,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "commit": "a1b2c3d4e5f6",
                        "deployed_at": "2026-07-09T12:00:00Z",
                        "version": "1.0.0",
                    }
                }
            }
        }
    },
)
async def health_version() -> VersionResponse:
    """Deployment identity for pipeline verification."""
    return VersionResponse(
        commit=settings.git_commit_sha,
        deployed_at=settings.deployed_at,
        version=settings.app_version,
    )

"""Scheduled operational tasks — DLQ watch, circuit monitor, periodic resets.

These are the platform's early-warning systems. None of them touch tenant
data paths; all run on the usage_tracking queue.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select, text

from app.core.ops import notify_ops
from app.core.redis import get_sync_redis
from app.worker.celery_app import DLQ_ALERT_THRESHOLD, DLQ_NAME, celery_app
from app.worker.db import worker_session

logger = logging.getLogger(__name__)


@celery_app.task(name="ops.check_dlq_size", queue="usage_tracking", ignore_result=True)
def check_dlq_size() -> int:
    """Every 15 minutes: a growing DLQ means a SYSTEMIC failure, not a blip."""
    size = int(cast("int", get_sync_redis().llen(DLQ_NAME)))
    logger.info("dlq size check", extra={"dlq_size": size})
    if size > DLQ_ALERT_THRESHOLD:
        notify_ops(f"DLQ has {size} items (threshold {DLQ_ALERT_THRESHOLD})")
    return size


@celery_app.task(name="ops.monitor_circuits", queue="usage_tracking", ignore_result=True)
def monitor_circuits() -> list[str]:
    """Every minute: log any open circuit breaker to Axiom."""

    async def _run() -> list[str]:
        from app.core.circuit import open_circuit_names

        return await open_circuit_names()

    open_names = asyncio.run(_run())
    if open_names:
        logger.error("open circuits", extra={"circuits": open_names})
    return open_names


@celery_app.task(name="billing.monthly_usage_reset", queue="usage_tracking", ignore_result=True)
def monthly_usage_reset() -> int:
    """Midnight UTC on the 1st: seed this month's MonthlyUsage row per active
    tenant so the very first quota check of the month never races row creation."""

    async def _run() -> int:
        from app.db.base import with_tenant_scope
        from app.db.models import Tenant, TenantStatus

        month = datetime.now(UTC).date().replace(day=1)
        created = 0
        async with worker_session() as session:
            tenant_ids = (
                await session.scalars(select(Tenant.id).where(Tenant.status == TenantStatus.ACTIVE))
            ).all()
            for tenant_id in tenant_ids:
                # monthly_usage is RLS-scoped; each insert needs tenant context
                async with with_tenant_scope(session, tenant_id):
                    await session.execute(
                        text(
                            "INSERT INTO monthly_usage (tenant_id, month) "
                            "VALUES (:tid, :month) ON CONFLICT (tenant_id, month) DO NOTHING"
                        ),
                        {"tid": tenant_id, "month": month},
                    )
                    await session.commit()
                created += 1
        return created

    count = asyncio.run(_run())
    logger.info("monthly usage reset complete", extra={"tenants": count})
    return count


@celery_app.task(
    name="onboarding.cleanup_expired_sessions", queue="usage_tracking", ignore_result=True
)
def cleanup_expired_sessions() -> int:
    """Daily 03:00 UTC: delete onboarding sessions past their expiry."""

    async def _run() -> int:
        async with worker_session() as session:
            result = await session.execute(
                text(
                    "DELETE FROM onboarding_sessions WHERE expires_at < now() "
                    "OR (expires_at IS NULL AND updated_at < now() - interval '48 hours')"
                )
            )
            await session.commit()
            return int(getattr(result, "rowcount", 0) or 0)

    deleted = asyncio.run(_run())
    logger.info("expired onboarding sessions removed", extra={"deleted": deleted})
    return deleted


@celery_app.task(name="credentials.health_check", queue="usage_tracking", ignore_result=True)
def credentials_health_check() -> int:
    """Weekly: re-verify every stored credential; surface expired tokens
    BEFORE they break a scheduled publish. Owner notification is a log/ops
    alert until the email phase lands."""

    async def _run() -> int:
        import httpx

        from app.db.base import with_tenant_scope
        from app.db.models import ApiCredential
        from app.modules.credentials.service import (
            _VERIFIERS,
            VERIFY_TIMEOUT_S,
            get_decrypted_credential,
        )

        failures = 0
        async with worker_session() as session:
            rows = (
                await session.execute(
                    text("SELECT DISTINCT tenant_id, service FROM api_credentials")
                )
            ).all()
            async with httpx.AsyncClient(timeout=VERIFY_TIMEOUT_S) as client:
                for tenant_id, service in rows:
                    verifier = _VERIFIERS.get(service)
                    if verifier is None:
                        continue
                    tid = uuid.UUID(str(tenant_id))
                    try:
                        async with with_tenant_scope(session, tid):
                            credential = await get_decrypted_credential(tid, service, session)
                            await session.commit()
                        await verifier(credential.fields, client)
                    except Exception as exc:  # noqa: BLE001 — one bad credential must not stop the sweep
                        failures += 1
                        logger.warning(
                            "credential health check failed",
                            extra={
                                "tenant_id": str(tid),
                                "service": service,
                                "error": str(exc)[:500],
                            },
                        )
        _ = ApiCredential  # imported for schema availability in tests
        return failures

    failures = asyncio.run(_run())
    if failures:
        notify_ops(f"credential health check: {failures} credential(s) failing verification")
    return failures


@celery_app.task(name="leads.followup_sequencing", queue="lead_outreach", ignore_result=True)
def followup_sequencing() -> None:
    """Every 5 minutes: find leads due for a follow-up and enqueue outreach.

    Stub until the outreach phase (Prompt 7) defines follow-up sequences —
    the schedule slot exists now so the cadence is already load-tested.
    """
    logger.debug("followup sequencing tick")


@celery_app.task(name="ads.sync_performance", queue="ad_management", ignore_result=True)
def sync_ad_performance() -> None:
    """Every 6 hours: pull Meta ad metrics for active campaigns.

    Stub until the ads phase defines campaign storage.
    """
    logger.debug("ad performance sync tick")

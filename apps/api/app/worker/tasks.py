"""Celery tasks for the onboarding/profile phase.

Tasks are synchronous Celery entry points that run their async body via
asyncio.run with a NullPool engine (workers are long-lived processes; no
event loop is shared between task invocations).
"""

import asyncio
import logging
import uuid
from typing import cast

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def _engine() -> "AsyncEngine":
    return create_async_engine(settings.pooled_database_url, poolclass=NullPool)


@celery_app.task(name="onboarding.persist_session", queue="usage_tracking", ignore_result=True)
def persist_onboarding_session(token: str, stage: str, answers: dict[str, object]) -> None:
    """Durability shadow-write of a Redis onboarding session."""

    async def _run() -> None:
        engine = _engine()
        async with AsyncSession(engine) as session:
            await session.execute(
                text(
                    "INSERT INTO onboarding_sessions (session_token, current_stage, data) "
                    "VALUES (:token, :stage, cast(:data AS jsonb)) "
                    "ON CONFLICT (session_token) DO UPDATE SET "
                    "current_stage = EXCLUDED.current_stage, data = EXCLUDED.data, "
                    "updated_at = now()"
                ),
                {
                    "token": token,
                    "stage": stage,
                    "data": __import__("json").dumps({"answers": answers}),
                },
            )
            await session.commit()
        await engine.dispose()

    asyncio.run(_run())


@celery_app.task(
    name="profiles.compute_nanobanana_style_prompt",
    queue="creative_generation",
    ignore_result=True,
)
def compute_nanobanana_style_prompt(tenant_id: str) -> None:
    """Pre-compute the image-generation style fragment from the brand kit.

    Triggered on onboarding completion and on every brand identity update,
    so image generation NEVER computes style on demand.
    [CANVA_NEXT_UPDATE] this same trigger will instead call the Canva brand
    kit creation API and store the Canva brand kit id.
    """

    async def _run() -> None:
        from app.db.base import with_tenant_scope
        from app.db.models import BrandKit, BusinessProfile
        from app.modules.profiles.categories import CATEGORIES

        engine = _engine()
        tid = uuid.UUID(tenant_id)
        async with AsyncSession(engine) as session:
            async with with_tenant_scope(session, tid):
                kit = await session.scalar(select(BrandKit))
                profile = await session.scalar(select(BusinessProfile))
                if kit is None:
                    logger.warning("no brand kit for tenant %s", tenant_id)
                    return
                colors = cast(dict[str, object], kit.colors or {})
                primary = str(colors.get("primary", "#111111"))
                secondary = str(colors.get("secondary", ""))
                style = str((kit.fonts or {}).get("design_style", "clean, modern"))
                category_notes = ""
                if profile is not None:
                    config = CATEGORIES.get(profile.category)
                    if config is not None:
                        category_notes = config.image_style_notes
                fragment = (
                    f"Brand palette: primary {primary}"
                    + (f", secondary {secondary}" if secondary else "")
                    + f". Design style: {style}. {category_notes}"
                ).strip()
                kit.nanobanana_style_prompt = fragment
                await session.commit()
        await engine.dispose()

    asyncio.run(_run())


@celery_app.task(
    name="credentials.register_platform_identifiers",
    queue="usage_tracking",
    ignore_result=True,
)
def register_platform_identifiers(tenant_id: str, service: str) -> None:
    """Fetch the tenant's public platform ids and upsert platform_identifiers.

    These rows are how incoming webhooks are routed to a tenant BEFORE any
    tenant context exists — they must exist as soon as a credential is saved.
    """

    async def _run() -> None:
        import httpx

        from app.db.base import with_tenant_scope
        from app.modules.credentials.service import get_decrypted_credential

        engine = _engine()
        tid = uuid.UUID(tenant_id)
        platform_map = {"meta": "meta", "instagram": "instagram", "whatsapp": "whatsapp"}
        platform = platform_map.get(service)
        if platform is None:
            return
        async with AsyncSession(engine) as session:
            async with with_tenant_scope(session, tid):
                credential = await get_decrypted_credential(tid, service, session)
                external_id = (
                    credential.fields.get("page_id")
                    or credential.fields.get("business_account_id")
                    or credential.fields.get("phone_number_id")
                )
                if not external_id:
                    return
                # Confirm the id is live on the platform before registering
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(
                        f"https://graph.facebook.com/v21.0/{external_id}",
                        params={"access_token": credential.fields.get("access_token", "")},
                    )
                    if response.status_code != 200:
                        logger.warning("identifier fetch failed", extra={"service": service})
                await session.execute(
                    text(
                        "INSERT INTO platform_identifiers (tenant_id, platform, external_id) "
                        "VALUES (:tid, :platform, :ext) ON CONFLICT DO NOTHING"
                    ),
                    {"tid": tid, "platform": platform, "ext": str(external_id)},
                )
                await session.commit()
        await engine.dispose()

    asyncio.run(_run())


@celery_app.task(
    name="leads.cancel_pending_outreach_for_tenant",
    queue="lead_outreach",
    ignore_result=True,
)
def cancel_pending_outreach_tasks_for_tenant(tenant_id: str) -> None:
    """Stub: cancels queued outreach when a credential is revoked.

    Real implementation lands with the outreach phase (Prompt 7) — revoking
    a credential must immediately stop any scheduled sends that would fail.
    """
    logger.info("outreach cancellation requested", extra={"tenant_id": tenant_id})

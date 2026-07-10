"""Post generation Celery task chain.

    generate_copy → generate_image → upload_to_r2 → notify_completion

Built with chain() so a failure in any step fails the whole chain cleanly —
no orphaned image generation for a post whose copy never validated.

Only (post_id, tenant_id) travel between tasks. Every step RE-FETCHES the
post from the database: a task can sit queued for minutes, and publishing
decisions must be made against the row as it is NOW, not as it was when the
chain was assembled. tenant_id must travel too — RLS makes the post row
invisible without tenant context.

Progress is tracked in Redis (gen_progress:{post_id}) through the stages
copy_generating → copy_done → image_generating → image_done → uploading →
complete | failed, for the frontend polling endpoint.
"""

import asyncio
import json
import logging
import uuid
from typing import Any

from celery import chain
from sqlalchemy import select

from app.core.exceptions import PlanLimitError, ResourceNotFoundError
from app.core.redis import get_sync_redis
from app.worker.celery_app import celery_app
from app.worker.db import worker_session

logger = logging.getLogger(__name__)

PROGRESS_TTL_S = 3600

Payload = dict[str, str]


def set_progress(post_id: str, stage: str, detail: dict[str, object] | None = None) -> None:
    get_sync_redis().set(
        f"gen_progress:{post_id}",
        json.dumps({"stage": stage, **(detail or {})}),
        ex=PROGRESS_TTL_S,
    )


def enqueue_post_generation(post_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    """Assemble and dispatch the four-step chain; returns the chain's task id."""
    payload: Payload = {"post_id": str(post_id), "tenant_id": str(tenant_id)}
    result = chain(
        generate_copy_task.s(payload),
        generate_image_task.s(),
        upload_to_r2_task.s(),
        notify_completion_task.s(),
    ).apply_async()
    set_progress(str(post_id), "copy_generating")
    return str(result.id)


async def _load_post(payload: Payload, session: Any) -> Any:  # noqa: ANN401
    from app.db.base import with_tenant_scope
    from app.db.models import Post

    tenant_id = uuid.UUID(payload["tenant_id"])
    post_id = uuid.UUID(payload["post_id"])
    async with with_tenant_scope(session, tenant_id):
        post = await session.scalar(select(Post).where(Post.id == post_id))
    if post is None:
        raise ResourceNotFoundError(f"post {post_id} not found")
    return post


@celery_app.task(name="posts.generate_copy", queue="creative_generation")
def generate_copy_task(payload: Payload) -> Payload:
    """Step 1: platform-aware copy on the tenant's key, written to the post row."""

    async def _run() -> None:
        from app.db.base import with_tenant_scope
        from app.modules.posts.copy_generation_service import generate_post_copy

        tenant_id = uuid.UUID(payload["tenant_id"])
        async with worker_session() as session:
            post = await _load_post(payload, session)
            meta = dict(post.meta or {})
            copy = await generate_post_copy(
                tenant_id=tenant_id,
                platform=str(meta.get("platform", "instagram")),
                topic=str(meta.get("topic", "")),
                session=session,
            )
            async with with_tenant_scope(session, tenant_id):
                post.content = copy.caption
                meta.update(
                    {
                        "hashtags": copy.hashtags,
                        "call_to_action": copy.call_to_action,
                        "image_description": copy.image_description,
                        "template_style": copy.template_style,
                    }
                )
                post.meta = meta
                await session.commit()

    try:
        asyncio.run(_run())
    except Exception:
        set_progress(payload["post_id"], "failed", {"failed_stage": "copy"})
        raise
    set_progress(payload["post_id"], "copy_done")
    return payload


@celery_app.task(name="posts.generate_image", queue="creative_generation")
def generate_image_task(payload: Payload) -> Payload:
    """Step 2: enforce the images quota, then generate + upload the creative."""
    set_progress(payload["post_id"], "image_generating")

    async def _run() -> str:
        from app.db.base import with_tenant_scope
        from app.db.models import Tenant
        from app.modules.billing.usage_service import check_and_increment_usage, upgrade_target
        from app.modules.images.client import image_client

        tenant_id = uuid.UUID(payload["tenant_id"])
        async with worker_session() as session:
            post = await _load_post(payload, session)
            meta = dict(post.meta or {})

            tenant = await session.scalar(select(Tenant).where(Tenant.id == tenant_id))
            if tenant is None:
                raise ResourceNotFoundError(f"tenant {tenant_id} not found")
            async with with_tenant_scope(session, tenant_id):
                decision = await check_and_increment_usage(
                    tenant_id, "images_generated", tenant.plan, session
                )
                await session.commit()
            if not decision.allowed:
                raise PlanLimitError(
                    "Monthly image generation limit reached",
                    current_count=decision.current,
                    limit=decision.limit or 0,
                    upgrade_to=upgrade_target(tenant.plan),
                )

            r2_key, _signed = await image_client.generate_image(
                tenant_id=tenant_id,
                content_description=str(meta.get("image_description", meta.get("topic", ""))),
                format=str(meta.get("format", "square")),
                session=session,
            )
            return r2_key

    try:
        payload["image_r2_key"] = asyncio.run(_run())
    except PlanLimitError:
        set_progress(
            payload["post_id"], "failed", {"failed_stage": "image", "reason": "usage_limit"}
        )
        raise
    except Exception:
        set_progress(payload["post_id"], "failed", {"failed_stage": "image"})
        raise
    set_progress(payload["post_id"], "image_done")
    return payload


@celery_app.task(name="posts.upload_to_r2", queue="creative_generation")
def upload_to_r2_task(payload: Payload) -> Payload:
    """Step 3: persist the R2 key on the (re-fetched) post row + fresh signed URL."""
    set_progress(payload["post_id"], "uploading")

    async def _run() -> str:
        from app.core.r2_service import r2_service
        from app.db.base import with_tenant_scope

        tenant_id = uuid.UUID(payload["tenant_id"])
        async with worker_session() as session:
            post = await _load_post(payload, session)
            async with with_tenant_scope(session, tenant_id):
                media = dict(post.media_urls or {})
                media["image_r2_key"] = payload["image_r2_key"]
                post.media_urls = media
                await session.commit()
        return await r2_service.generate_signed_url(payload["image_r2_key"])

    try:
        payload["signed_url"] = asyncio.run(_run())
    except Exception:
        set_progress(payload["post_id"], "failed", {"failed_stage": "upload"})
        raise
    return payload


@celery_app.task(name="posts.notify_completion", queue="usage_tracking")
def notify_completion_task(payload: Payload) -> Payload:
    """Step 4: mark complete and push the post_generated event to the frontend."""
    from app.modules.realtime.events import EventEmitter

    set_progress(
        payload["post_id"],
        "complete",
        {"signed_url": payload.get("signed_url", "")},
    )
    EventEmitter.emit_sync(
        payload["tenant_id"],
        "post_generated",
        {"post_id": payload["post_id"], "signed_url": payload.get("signed_url", "")},
    )
    return payload

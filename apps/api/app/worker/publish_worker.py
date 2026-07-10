"""Post publishing tasks — the idempotent bridge from schedule to platform.

Idempotency contract (DoD: running the same publish task twice results in
exactly ONE published post):
1. The task re-reads the post's status FIRST — already published → log a
   warning and return immediately.
2. Per-platform: a platform that already has an id in platform_post_ids is
   skipped, so a retry after a partial multi-platform publish only publishes
   the missing platforms.

Retry contract:
- PERMANENT PublishError (token expired, page gone) → status=failed, NO retry
- TRANSIENT PublishError / ExternalAPIError → exponential backoff, max 3
- CircuitOpenError → retry in 60s (fail fast now; the circuit gates the rush)
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from celery import Task
from sqlalchemy import select

from app.core.exceptions import CircuitOpenError, ExternalAPIError
from app.worker.celery_app import celery_app
from app.worker.db import worker_session

logger = logging.getLogger(__name__)

MAX_PUBLISH_RETRIES = 3

# post.platforms key → credential service name
_CREDENTIAL_SERVICE: dict[str, str] = {
    "facebook": "meta",
    "instagram": "instagram",
    "tiktok": "tiktok",
    "linkedin": "linkedin",
}


@celery_app.task(name="posts.check_scheduled", queue="post_publishing", ignore_result=True)
def check_scheduled_posts() -> int:
    """Beat, every minute: move due scheduled posts into the publish queue.

    RLS makes a global scan return nothing, so this iterates active tenants
    and scans inside each tenant's scope — at the current tenant count that
    is well under a second per tick; revisit with a SECURITY DEFINER scan
    function when tenants × posts grows."""

    async def _run() -> list[tuple[str, str]]:
        from app.db.base import with_tenant_scope
        from app.db.models import Post, PostStatus, Tenant, TenantStatus

        due: list[tuple[str, str]] = []
        async with worker_session() as session:
            tenant_ids = (
                await session.scalars(select(Tenant.id).where(Tenant.status == TenantStatus.ACTIVE))
            ).all()
            now = datetime.now(UTC)
            for tenant_id in tenant_ids:
                async with with_tenant_scope(session, tenant_id):
                    posts = (
                        await session.scalars(
                            select(Post).where(
                                Post.status == PostStatus.SCHEDULED,
                                Post.scheduled_at <= now,
                            )
                        )
                    ).all()
                    for post in posts:
                        # Claim it NOW so next minute's tick can't double-enqueue
                        post.status = PostStatus.PUBLISHING
                        due.append((str(post.id), str(tenant_id)))
                    await session.commit()
        return due

    due_posts = asyncio.run(_run())
    for post_id, tenant_id in due_posts:
        publish_post.delay({"post_id": post_id, "tenant_id": tenant_id})
    if due_posts:
        logger.info("scheduled posts enqueued", extra={"count": len(due_posts)})
    return len(due_posts)


@celery_app.task(
    name="posts.publish",
    queue="post_publishing",
    bind=True,
    max_retries=MAX_PUBLISH_RETRIES,
)
def publish_post(self: Task, payload: dict[str, str]) -> None:
    """Publish one post to every platform it targets. Safe to run twice."""
    from app.modules.posts.publishers.base import PublishError

    async def _run() -> None:
        from app.db.base import with_tenant_scope
        from app.db.models import Post, PostStatus
        from app.modules.credentials.service import get_decrypted_credential
        from app.modules.posts.publishers import PUBLISHERS
        from app.modules.realtime.events import EventEmitter

        tenant_id = uuid.UUID(payload["tenant_id"])
        post_id = uuid.UUID(payload["post_id"])

        async with worker_session() as session:
            async with with_tenant_scope(session, tenant_id):
                post = await session.scalar(select(Post).where(Post.id == post_id))
                if post is None:
                    logger.warning("publish: post vanished", extra={"post_id": str(post_id)})
                    return

                # ── Idempotency check: state BEFORE action ──
                if post.status == PostStatus.PUBLISHED:
                    logger.warning(
                        "publish skipped: already published",
                        extra={"post_id": str(post_id)},
                    )
                    return
                post.status = PostStatus.PUBLISHING
                await session.commit()

                platform_ids = dict(post.platform_post_ids or {})
                targets = [p for p, enabled in (post.platforms or {}).items() if enabled]
                for platform in targets:
                    if platform in platform_ids:  # this platform already succeeded
                        continue
                    publisher = PUBLISHERS.get(platform)
                    service = _CREDENTIAL_SERVICE.get(platform)
                    if publisher is None or service is None:
                        logger.warning("no publisher for platform", extra={"platform": platform})
                        continue
                    credential = await get_decrypted_credential(tenant_id, service, session)
                    await session.commit()  # decrypt is audit-logged inside
                    result = await publisher.publish(credential, post)
                    platform_ids[platform] = result.platform_post_id
                    post.platform_post_ids = platform_ids
                    await session.commit()  # persist per-platform progress immediately

                post.status = PostStatus.PUBLISHED
                post.published_at = datetime.now(UTC)
                post.error = None
                await session.commit()
                EventEmitter.emit_sync(
                    str(tenant_id),
                    "post_published",
                    {"post_id": str(post_id), "platforms": list(platform_ids)},
                )

    try:
        asyncio.run(_run())
    except PublishError as exc:
        if exc.is_retryable and self.request.retries < MAX_PUBLISH_RETRIES:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
        _mark_failed(payload, f"{exc.error_code}: {exc.error_message} ({exc.recovery_action})")
        if exc.is_retryable:
            raise  # retries exhausted → terminal failure → DLQ
    except CircuitOpenError as exc:
        raise self.retry(exc=exc, countdown=60) from exc
    except ExternalAPIError as exc:
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc


def _mark_failed(payload: dict[str, str], error: str) -> None:
    """Permanent failure: record the reason and notify the frontend."""

    async def _run() -> None:
        from app.db.base import with_tenant_scope
        from app.db.models import Post, PostStatus
        from app.modules.realtime.events import EventEmitter

        tenant_id = uuid.UUID(payload["tenant_id"])
        async with worker_session() as session:
            async with with_tenant_scope(session, tenant_id):
                post = await session.scalar(
                    select(Post).where(Post.id == uuid.UUID(payload["post_id"]))
                )
                if post is None:
                    return
                post.status = PostStatus.FAILED
                post.error = error[:2000]
                await session.commit()
        EventEmitter.emit_sync(
            payload["tenant_id"],
            "post_failed",
            {"post_id": payload["post_id"], "error": error[:500]},
        )

    asyncio.run(_run())

"""Post generation endpoints — the API side of the Celery chain."""

import json
import logging
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.exceptions import PlanLimitError, ResourceNotFoundError
from app.core.permissions import Permission
from app.core.redis import get_redis
from app.db.models import Post, PostStatus
from app.gateway.dependencies import CurrentUser, ScopedSession, check_permission
from app.modules.billing.usage_service import check_and_increment_usage, upgrade_target

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["posts"])


class GeneratePostRequest(BaseModel):
    platform: Literal["instagram", "facebook", "linkedin", "tiktok"]
    topic: str = Field(min_length=3, max_length=500)
    format: Literal["square", "portrait", "story", "landscape"] = "square"
    scheduled_at: datetime | None = None


@router.post(
    "/generate",
    status_code=202,
    summary="Generate post copy + creative via the background chain",
    dependencies=[Depends(check_permission(Permission.POSTS_CREATE))],
)
async def generate_post(
    body: GeneratePostRequest, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    from app.db.models import Plan

    decision = await check_and_increment_usage(
        user.tenant_id, "posts_generated", Plan(user.plan), session
    )
    if not decision.allowed:
        raise PlanLimitError(
            "Monthly post generation limit reached",
            current_count=decision.current,
            limit=decision.limit or 0,
            upgrade_to=upgrade_target(Plan(user.plan)),
        )

    post = Post(
        tenant_id=user.tenant_id,
        status=PostStatus.SCHEDULED if body.scheduled_at else PostStatus.DRAFT,
        platforms={body.platform: True},
        scheduled_at=body.scheduled_at,
        meta={"topic": body.topic, "platform": body.platform, "format": body.format},
    )
    session.add(post)
    await session.flush()

    from app.worker.post_worker import enqueue_post_generation

    chain_id = enqueue_post_generation(post.id, user.tenant_id)
    return {"post_id": str(post.id), "chain_task_id": chain_id, "status": "queued"}


@router.get("/{post_id}/progress", summary="Poll generation progress")
async def generation_progress(
    post_id: uuid.UUID, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    raw = await get_redis().get(f"gen_progress:{post_id}")
    if raw:
        progress: dict[str, object] = json.loads(raw)
        return {"post_id": str(post_id), **progress}
    # Progress key expired (1h TTL) — fall back to the durable post status
    post = await session.scalar(select(Post).where(Post.id == post_id))
    if post is None:
        raise ResourceNotFoundError(f"No post {post_id}")
    return {"post_id": str(post_id), "stage": post.status.value}

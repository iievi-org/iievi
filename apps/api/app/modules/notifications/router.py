"""In-app notification endpoints — Prompt 7 Step 8.

GET  /api/v1/notifications           unread, paginated
PATCH /api/v1/notifications/{id}/read
PATCH /api/v1/notifications/read-all

All are scoped to the authenticated user's own notifications; RLS additionally
confines them to the tenant. Read-state changes emit ``notification_count_changed``
so the sidebar badge updates over WebSocket in real time.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.exceptions import ResourceNotFoundError
from app.gateway.dependencies import CurrentUser, ScopedSession
from app.modules.notifications import service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", summary="List unread in-app notifications (paginated)")
async def list_notifications(
    user: CurrentUser,
    session: ScopedSession,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=service.MAX_PAGE_SIZE)] = service.DEFAULT_PAGE_SIZE,
) -> dict[str, object]:
    page, next_cursor = await service.list_unread(
        session, user_id=user.user_id, limit=limit, cursor=cursor
    )
    unread = await service.unread_count(session, user_id=user.user_id)
    return {
        "notifications": [service.serialize(n) for n in page],
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None,
        "unread": unread,
    }


@router.patch("/read-all", summary="Mark all notifications read")
async def mark_all_notifications_read(
    user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    marked = await service.mark_all_read(session, tenant_id=user.tenant_id, user_id=user.user_id)
    return {"marked": marked}


@router.patch("/{notification_id}/read", summary="Mark one notification read")
async def mark_notification_read(
    notification_id: uuid.UUID, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    changed = await service.mark_read(
        session,
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        notification_id=notification_id,
    )
    if not changed:
        raise ResourceNotFoundError(f"No unread notification {notification_id}")
    return {"read": True}

"""Notification preference endpoint — Prompt 7 Step 10.

PATCH /api/v1/users/notification-preferences updates per-channel toggles
(in_app / email / whatsapp), per-type overrides, and the quiet-hours window.
Only the fields present in the request are changed; the row is created on first
write. RLS confines the row to the tenant, and the unique (tenant_id, user_id)
constraint makes it the caller's own preferences.
"""

import datetime as dt

from fastapi import APIRouter
from sqlalchemy import select

from app.core.exceptions import BadRequestError
from app.core.schemas import SanitizedModel
from app.db.models import AuditAction, NotificationPreference
from app.gateway.dependencies import CurrentUser, ScopedSession
from app.modules.audit.service import log_event

router = APIRouter(prefix="/users", tags=["notifications"])


class NotificationPreferencesUpdate(SanitizedModel):
    """All fields optional — only those present in the request are applied."""

    email_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    in_app_enabled: bool | None = None
    # {notification_type: {channel: bool}}, e.g. {"new_lead": {"whatsapp": false}}
    overrides: dict[str, dict[str, bool]] | None = None
    quiet_hours_start: dt.time | None = None
    quiet_hours_end: dt.time | None = None
    quiet_hours_days: list[int] | None = None  # ISO weekdays 1-7; [] = every day


@router.patch("/notification-preferences", summary="Update notification preferences")
async def update_notification_preferences(
    body: NotificationPreferencesUpdate, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    provided = body.model_dump(exclude_unset=True)
    if not provided:
        raise BadRequestError("No preference fields to update")

    days = provided.get("quiet_hours_days")
    if isinstance(days, list) and any(not 1 <= int(d) <= 7 for d in days):
        raise BadRequestError("quiet_hours_days must be ISO weekday numbers 1-7")

    pref = await session.scalar(
        select(NotificationPreference).where(NotificationPreference.user_id == user.user_id)
    )
    created = pref is None
    if pref is None:
        pref = NotificationPreference(tenant_id=user.tenant_id, user_id=user.user_id)
        session.add(pref)
    for field, value in provided.items():
        setattr(pref, field, value)
    await session.flush()

    await log_event(
        session,
        action=AuditAction.UPDATE,
        resource_type="NotificationPreference",
        resource_id=pref.id,
        tenant_id=user.tenant_id,
        actor_user_id=user.user_id,
        new_values={"updated": sorted(provided.keys()), "created": created},
    )
    return {"updated": sorted(provided.keys())}

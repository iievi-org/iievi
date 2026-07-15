"""In-app notification store + dispatch — Prompt 7 Steps 8 & 10.

The in-app half (Step 8): create/list/mark notifications for the dashboard bell.
Every write that changes a user's unread count emits a
``notification_count_changed`` WebSocket event so the badge updates in real time.

The dispatch half (Step 10): ``dispatch`` is the single entry point every
notification producer calls. It honours per-type, per-channel preferences and
quiet hours — a notification due inside quiet hours is queued for delivery when
the window ends rather than sent immediately.

All functions operate inside an active tenant scope (``notifications`` and
``notification_preferences`` are RLS-protected) and never commit — they join the
caller's transaction.
"""

import base64
import datetime as dt
import logging
import uuid
from datetime import UTC, datetime, timedelta, timezone
from typing import Any, cast

from sqlalchemy import func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ExternalAPIError
from app.db.base import with_tenant_scope
from app.db.models import Notification, NotificationPreference, NotificationType
from app.modules.realtime.events import EventEmitter

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Quiet hours are evaluated in the platform's primary market timezone (IST).
_IST = timezone(timedelta(hours=5, minutes=30))
_ALL_CHANNELS: tuple[str, ...] = ("in_app", "email", "whatsapp")


# ---------------------------------------------------------------------------
# Cursor helpers (created_at desc, id desc)
# ---------------------------------------------------------------------------


def _encode_cursor(created_at: datetime, notif_id: uuid.UUID) -> str:
    return base64.urlsafe_b64encode(f"{created_at.isoformat()}|{notif_id}".encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    ts, _, notif_id = raw.partition("|")
    return datetime.fromisoformat(ts), uuid.UUID(notif_id)


# ---------------------------------------------------------------------------
# In-app store (Step 8)
# ---------------------------------------------------------------------------


async def unread_count(session: AsyncSession, *, user_id: uuid.UUID) -> int:
    """Number of unread notifications for a user."""
    total = await session.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
    )
    return int(total or 0)


async def _emit_count_changed(
    session: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    count = await unread_count(session, user_id=user_id)
    await EventEmitter.emit(
        tenant_id, "notification_count_changed", {"user_id": str(user_id), "unread": count}
    )


async def create_notification(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    notif_type: NotificationType,
    title: str,
    body: str,
    action_url: str | None = None,
) -> uuid.UUID:
    """Insert an in-app notification and emit the updated unread count."""
    notif = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        type=notif_type,
        title=title,
        body=body,
        action_url=action_url,
    )
    session.add(notif)
    await session.flush()
    await _emit_count_changed(session, tenant_id, user_id)
    logger.info(
        "notification created",
        extra={"tenant_id": str(tenant_id), "user_id": str(user_id), "type": notif_type.value},
    )
    return notif.id


async def list_unread(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    limit: int = DEFAULT_PAGE_SIZE,
    cursor: str | None = None,
) -> tuple[list[Notification], str | None]:
    """Return (page, next_cursor) of unread notifications, newest first."""
    query = (
        select(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    )
    if cursor:
        cursor_ts, cursor_id = _decode_cursor(cursor)
        query = query.where(
            (Notification.created_at < cursor_ts)
            | ((Notification.created_at == cursor_ts) & (Notification.id < cursor_id))
        )
    rows = list((await session.scalars(query.limit(limit + 1))).all())
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = _encode_cursor(page[-1].created_at, page[-1].id) if has_more and page else None
    return page, next_cursor


async def mark_read(
    session: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID, notification_id: uuid.UUID
) -> bool:
    """Mark one notification read (only the owner's). Returns True if it changed."""
    result = await session.execute(
        update(Notification)
        .where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        .values(read_at=datetime.now(UTC))
    )
    changed = bool(cast("CursorResult[Any]", result).rowcount)
    if changed:
        await _emit_count_changed(session, tenant_id, user_id)
    return changed


async def mark_all_read(session: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID) -> int:
    """Mark all of a user's unread notifications read; return how many changed."""
    result = await session.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    marked = int(cast("CursorResult[Any]", result).rowcount or 0)
    if marked:
        await _emit_count_changed(session, tenant_id, user_id)
    return marked


def serialize(notif: Notification) -> dict[str, object]:
    return {
        "id": str(notif.id),
        "type": notif.type.value,
        "title": notif.title,
        "body": notif.body,
        "action_url": notif.action_url,
        "read_at": notif.read_at.isoformat() if notif.read_at else None,
        "created_at": notif.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Dispatch with preferences + quiet hours (Step 10)
# ---------------------------------------------------------------------------


class _DefaultPrefs:
    """Stand-in when a user has no NotificationPreference row: every channel on,
    no quiet hours."""

    email_enabled = True
    whatsapp_enabled = True
    in_app_enabled = True
    overrides: dict[str, object] = {}
    quiet_hours_start: dt.time | None = None
    quiet_hours_end: dt.time | None = None
    quiet_hours_days: list[int] = []


Prefs = NotificationPreference | _DefaultPrefs


async def _load_prefs(session: AsyncSession, user_id: uuid.UUID) -> Prefs:
    pref = await session.scalar(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    return pref or _DefaultPrefs()


def _channel_enabled(prefs: Prefs, notif_type: NotificationType, channel: str) -> bool:
    """A channel fires if the per-type override says so, else the base flag."""
    overrides = prefs.overrides if isinstance(prefs.overrides, dict) else {}
    type_override = overrides.get(notif_type.value, {})
    if isinstance(type_override, dict) and channel in type_override:
        return bool(type_override[channel])
    base = {
        "in_app": prefs.in_app_enabled,
        "email": prefs.email_enabled,
        "whatsapp": prefs.whatsapp_enabled,
    }
    return bool(base[channel])


def _enabled_channels(prefs: Prefs, notif_type: NotificationType) -> list[str]:
    return [c for c in _ALL_CHANNELS if _channel_enabled(prefs, notif_type, c)]


def _in_quiet_hours(prefs: Prefs, now_ist: datetime) -> bool:
    if prefs.quiet_hours_start is None or prefs.quiet_hours_end is None:
        return False
    days = list(prefs.quiet_hours_days or [])
    if days and now_ist.isoweekday() not in days:
        return False
    start, end, current = prefs.quiet_hours_start, prefs.quiet_hours_end, now_ist.time()
    if start <= end:
        return start <= current < end
    return current >= start or current < end  # overnight window (e.g. 22:00-07:00)


def _seconds_until_quiet_end(prefs: Prefs, now_ist: datetime) -> int:
    end = prefs.quiet_hours_end
    if end is None:
        return 0
    target = now_ist.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
    if target <= now_ist:
        target += timedelta(days=1)
    return int((target - now_ist).total_seconds())


async def dispatch(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    notif_type: NotificationType,
    title: str,
    body: str,
    action_url: str | None = None,
    email_to: str | None = None,
    whatsapp_to: str | None = None,
    business_name: str | None = None,
) -> str:
    """Route a notification to the channels the user's prefs enable, honoring
    quiet hours. Returns "sent" | "deferred" | "skipped". Runs in the caller's
    transaction (does not commit)."""
    prefs = await _load_prefs(session, user_id)
    channels = _enabled_channels(prefs, notif_type)
    if not channels:
        return "skipped"

    now_ist = datetime.now(_IST)
    if _in_quiet_hours(prefs, now_ist):
        delay = _seconds_until_quiet_end(prefs, now_ist)
        _enqueue_deferred(
            {
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "type": notif_type.value,
                "title": title,
                "body": body,
                "action_url": action_url,
                "channels": channels,
                "email_to": email_to,
                "whatsapp_to": whatsapp_to,
                "business_name": business_name,
            },
            delay,
        )
        logger.info(
            "notification deferred for quiet hours",
            extra={"user_id": str(user_id), "type": notif_type.value, "delay_s": delay},
        )
        return "deferred"

    await deliver_channels(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        notif_type=notif_type,
        title=title,
        body=body,
        channels=channels,
        action_url=action_url,
        email_to=email_to,
        whatsapp_to=whatsapp_to,
        business_name=business_name,
    )
    return "sent"


async def deliver_channels(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    notif_type: NotificationType,
    title: str,
    body: str,
    channels: list[str],
    action_url: str | None = None,
    email_to: str | None = None,
    whatsapp_to: str | None = None,
    business_name: str | None = None,
) -> None:
    """Deliver immediately to the given channels (no prefs/quiet-hours check).

    Shared by ``dispatch`` (inline) and the deferred-delivery worker task.
    """
    if "in_app" in channels:
        async with with_tenant_scope(session, tenant_id):
            await create_notification(
                session,
                tenant_id=tenant_id,
                user_id=user_id,
                notif_type=notif_type,
                title=title,
                body=body,
                action_url=action_url,
            )
    if "email" in channels and email_to:
        from app.modules.notifications.email_service import NotificationEmail, send_email

        try:
            await send_email(
                NotificationEmail(
                    to=email_to,
                    business_name=business_name or "your business",
                    title=title,
                    body=body,
                    action_url=action_url or settings.dashboard_url,
                )
            )
        except ExternalAPIError:
            logger.warning("notification email failed", extra={"user_id": str(user_id)})
    if "whatsapp" in channels and whatsapp_to:
        from app.modules.notifications.whatsapp_channel import send_owner_whatsapp

        await send_owner_whatsapp(whatsapp_to, f"{title}\n\n{body}")


def _enqueue_deferred(payload: dict[str, object], delay: int) -> None:
    from app.worker.notification_worker import deliver_deferred_notification

    deliver_deferred_notification.apply_async(args=[payload], countdown=delay)

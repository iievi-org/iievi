"""Notification preferences + quiet-hours DoD (Prompt 7 Step 10) — pure logic."""

import datetime as dt
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.db.models import NotificationType
from app.modules.notifications import service

IST = timezone(timedelta(hours=5, minutes=30))


def prefs(**kw: object) -> SimpleNamespace:
    base: dict[str, object] = {
        "email_enabled": True,
        "whatsapp_enabled": True,
        "in_app_enabled": True,
        "overrides": {},
        "quiet_hours_start": None,
        "quiet_hours_end": None,
        "quiet_hours_days": [],
    }
    base.update(kw)
    return SimpleNamespace(**base)


def at(hour: int, minute: int = 0) -> datetime:
    # 2026-07-15 is a Wednesday (isoweekday 3).
    return datetime(2026, 7, 15, hour, minute, tzinfo=IST)


def _aload(p: object) -> Callable[..., Awaitable[object]]:
    async def _inner(*_a: object, **_k: object) -> object:
        return p

    return _inner


def test_same_day_quiet_window() -> None:
    p = prefs(quiet_hours_start=dt.time(9, 0), quiet_hours_end=dt.time(17, 0))
    assert service._in_quiet_hours(p, at(10)) is True
    assert service._in_quiet_hours(p, at(18)) is False


def test_overnight_quiet_window() -> None:
    p = prefs(quiet_hours_start=dt.time(22, 0), quiet_hours_end=dt.time(7, 0))
    assert service._in_quiet_hours(p, at(23)) is True
    assert service._in_quiet_hours(p, at(2)) is True
    assert service._in_quiet_hours(p, at(12)) is False


def test_quiet_days_restrict_to_listed_weekdays() -> None:
    # Weekend-only quiet hours; the test date is a Wednesday.
    p = prefs(
        quiet_hours_start=dt.time(22, 0), quiet_hours_end=dt.time(7, 0), quiet_hours_days=[6, 7]
    )
    assert service._in_quiet_hours(p, at(23)) is False


def test_seconds_until_quiet_end() -> None:
    p = prefs(quiet_hours_end=dt.time(7, 0))
    assert service._seconds_until_quiet_end(p, at(2)) == 5 * 3600


def test_enabled_channels_respects_base_flags_and_overrides() -> None:
    p = prefs(overrides={"new_lead": {"whatsapp": False}})
    channels = service._enabled_channels(p, NotificationType.NEW_LEAD)
    assert "in_app" in channels and "email" in channels and "whatsapp" not in channels

    p2 = prefs(email_enabled=False)
    assert "email" not in service._enabled_channels(p2, NotificationType.NEW_LEAD)


async def test_dispatch_defers_during_quiet_hours(monkeypatch: object) -> None:
    monkeypatch.setattr(service, "_load_prefs", _aload(prefs()))  # type: ignore[attr-defined]
    monkeypatch.setattr(service, "_in_quiet_hours", lambda _p, _n: True)  # type: ignore[attr-defined]
    captured: dict[str, object] = {}
    monkeypatch.setattr(  # type: ignore[attr-defined]
        service,
        "_enqueue_deferred",
        lambda payload, delay: captured.update(payload=payload, delay=delay),
    )
    delivered: list[object] = []

    async def _fake_deliver(*_a: object, **_k: object) -> None:
        delivered.append(_k)

    monkeypatch.setattr(service, "deliver_channels", _fake_deliver)  # type: ignore[attr-defined]

    result = await service.dispatch(
        MagicMock(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        notif_type=NotificationType.NEW_LEAD,
        title="A new lead",
        body="Riya messaged you",
    )
    assert result == "deferred"
    assert isinstance(captured["payload"], dict)
    assert captured["payload"]["title"] == "A new lead"
    assert not delivered  # nothing delivered now


async def test_dispatch_delivers_outside_quiet_hours(monkeypatch: object) -> None:
    monkeypatch.setattr(service, "_load_prefs", _aload(prefs()))  # type: ignore[attr-defined]
    monkeypatch.setattr(service, "_in_quiet_hours", lambda _p, _n: False)  # type: ignore[attr-defined]
    delivered: list[object] = []

    async def _fake_deliver(_session: object, **kwargs: object) -> None:
        delivered.append(kwargs)

    monkeypatch.setattr(service, "deliver_channels", _fake_deliver)  # type: ignore[attr-defined]

    result = await service.dispatch(
        MagicMock(),
        tenant_id=uuid4(),
        user_id=uuid4(),
        notif_type=NotificationType.NEW_LEAD,
        title="A new lead",
        body="Riya messaged you",
    )
    assert result == "sent"
    assert delivered

"""Publishers: error classification, publish idempotency (DoD: running the
same publish task twice → exactly one published post), WhatsApp 24h window,
TikTok WhatsApp deep-link contract."""

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.core.exceptions import WhatsAppSessionExpiredError
from app.modules.credentials.service import DecryptedCredential
from app.modules.posts.publishers.base import classify_error

TENANT_ID = uuid.uuid4()
POST_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Error classification — permanent vs transient is load-bearing
# ---------------------------------------------------------------------------


def test_meta_token_expired_is_permanent() -> None:
    error = classify_error("facebook", 190, "token expired")
    assert error.error_code == "TOKEN_EXPIRED"
    assert error.is_retryable is False


def test_meta_rate_limit_is_transient() -> None:
    error = classify_error("instagram", 4, "too many calls")
    assert error.error_code == "RATE_LIMIT_EXCEEDED"
    assert error.is_retryable is True


def test_tiktok_invalid_token_is_permanent() -> None:
    error = classify_error("tiktok", "access_token_invalid")
    assert error.is_retryable is False


def test_linkedin_429_is_transient_and_401_permanent() -> None:
    assert classify_error("linkedin", 429).is_retryable is True
    assert classify_error("linkedin", 401).is_retryable is False


def test_unknown_code_defaults_to_transient() -> None:
    error = classify_error("facebook", 99999, "novel error")
    assert error.is_retryable is True
    assert error.error_code.startswith("UNKNOWN_")


# ---------------------------------------------------------------------------
# Publish idempotency (DoD)
# ---------------------------------------------------------------------------


class _ExplodingPublisher:
    platform = "facebook"

    async def publish(self, *_a: object, **_k: object) -> None:
        raise AssertionError("publisher must not run for an already-published post")


def test_publish_task_skips_already_published_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD: the same publish task run twice results in exactly one publish —
    the second run sees status=published and returns without touching any
    publisher."""
    import app.db.base as db_base
    from app.db.models import PostStatus
    from app.worker import publish_worker

    published_post = SimpleNamespace(
        id=POST_ID,
        status=PostStatus.PUBLISHED,
        platforms={"facebook": True},
        platform_post_ids={"facebook": "fb_123"},
    )

    class _Session:
        async def scalar(self, *_a: object, **_k: object) -> object:
            return published_post

        async def commit(self) -> None:  # pragma: no cover - not reached
            raise AssertionError("nothing must be written for a published post")

    session = _Session()

    @asynccontextmanager
    async def _fake_worker_session():  # noqa: ANN202
        yield session

    @asynccontextmanager
    async def _fake_scope(*_a: object, **_k: object):  # noqa: ANN202
        yield session

    monkeypatch.setattr(publish_worker, "worker_session", _fake_worker_session)
    monkeypatch.setattr(db_base, "with_tenant_scope", _fake_scope)

    from app.modules.posts import publishers

    monkeypatch.setitem(publishers.PUBLISHERS, "facebook", _ExplodingPublisher())  # type: ignore[misc]

    # .run() executes the task body without a broker
    publish_worker.publish_post.run({"post_id": str(POST_ID), "tenant_id": str(TENANT_ID)})
    # Reaching here without AssertionError = the publisher was never invoked
    assert published_post.platform_post_ids == {"facebook": "fb_123"}


# ---------------------------------------------------------------------------
# WhatsApp 24-hour session window
# ---------------------------------------------------------------------------

_CREDENTIAL = DecryptedCredential(
    service="whatsapp",
    fields={"access_token": "secret-token", "phone_number_id": "12345"},
)


async def test_session_message_blocked_outside_window() -> None:
    from app.modules.channels.whatsapp_client import send_session_message

    stale = datetime.now(UTC) - timedelta(hours=25)
    with pytest.raises(WhatsAppSessionExpiredError):
        await send_session_message("+919876543210", "hello", _CREDENTIAL, last_inbound_at=stale)


async def test_session_message_blocked_with_no_inbound_ever() -> None:
    from app.modules.channels.whatsapp_client import send_session_message

    with pytest.raises(WhatsAppSessionExpiredError):
        await send_session_message("+919876543210", "hello", _CREDENTIAL, last_inbound_at=None)


def test_window_open_within_24_hours() -> None:
    from app.modules.channels.whatsapp_client import session_window_open

    assert session_window_open(datetime.now(UTC) - timedelta(hours=23))
    assert not session_window_open(datetime.now(UTC) - timedelta(hours=25))


# ---------------------------------------------------------------------------
# TikTok caption contract: WhatsApp deep link is ALWAYS the final line
# ---------------------------------------------------------------------------


def test_tiktok_caption_ends_with_whatsapp_link() -> None:
    from app.modules.posts.publishers.tiktok import TikTokPublisher

    post = SimpleNamespace(
        content="Fresh fades all week",
        meta={"hashtags": ["#barber", "#fade"]},
    )
    caption = TikTokPublisher.build_caption(post, "https://wa.me/919876543210")
    assert caption.splitlines()[-1] == "https://wa.me/919876543210"
    assert "#barber" in caption

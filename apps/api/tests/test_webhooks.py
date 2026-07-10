"""Webhook receivers: signature verification (DoD: invalid signature → 401),
Stripe/Razorpay verifiers, Facebook comment two-action handler (DoD: one
public reply call + one Messenger DM call)."""

import hashlib
import hmac
import json
import time
import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.exceptions import WebhookSignatureError
from app.main import app

TENANT_ID = uuid.uuid4()

META_SECRET = "meta-test-secret"  # noqa: S105 — deliberately fake
RAZORPAY_SECRET = "razorpay-test-secret"  # noqa: S105
STRIPE_SECRET = "stripe-test-secret"  # noqa: S105


def _patched_settings(**overrides: str) -> object:
    """Settings is frozen — swap the module-level reference with a clone."""
    values = {
        "meta_app_secret": META_SECRET,
        "razorpay_webhook_secret": RAZORPAY_SECRET,
        "stripe_webhook_secret": STRIPE_SECRET,
        "meta_webhook_verify_token": settings.meta_webhook_verify_token,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from app.modules.webhooks import billing_router, meta_router

    monkeypatch.setattr(meta_router, "settings", _patched_settings())
    monkeypatch.setattr(billing_router, "settings", _patched_settings())
    return TestClient(app)


def _meta_signature(body: bytes, secret: str = META_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Signature verification — the DoD 401 checks
# ---------------------------------------------------------------------------


def test_meta_webhook_invalid_signature_returns_401(client: TestClient) -> None:
    body = json.dumps({"object": "page", "entry": []}).encode()
    response = client.post(
        "/api/v1/webhooks/meta",
        content=body,
        headers={"X-Hub-Signature-256": "sha256=deadbeef"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "webhook_signature_invalid"


def test_meta_webhook_missing_signature_returns_401(client: TestClient) -> None:
    response = client.post("/api/v1/webhooks/meta", content=b"{}")
    assert response.status_code == 401


def test_razorpay_invalid_signature_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/webhooks/razorpay",
        content=b'{"event": "subscription.charged"}',
        headers={"X-Razorpay-Signature": "bogus"},
    )
    assert response.status_code == 401


def test_stripe_invalid_signature_returns_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/webhooks/stripe",
        content=b'{"id": "evt_1", "type": "invoice.payment_succeeded"}',
        headers={"Stripe-Signature": "t=123,v1=bogus"},
    )
    assert response.status_code == 401


def test_meta_signature_verifier_accepts_valid_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.webhooks import meta_router

    monkeypatch.setattr(meta_router, "settings", _patched_settings())
    body = b'{"object": "page"}'
    meta_router.verify_meta_signature(body, _meta_signature(body))  # must not raise


def test_stripe_signature_verifier_full_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.webhooks import billing_router

    monkeypatch.setattr(billing_router, "settings", _patched_settings())
    body = b'{"id": "evt_1"}'
    timestamp = str(int(time.time()))
    signed = f"{timestamp}.".encode() + body
    sig = hmac.new(STRIPE_SECRET.encode(), signed, hashlib.sha256).hexdigest()

    billing_router.verify_stripe_signature(body, f"t={timestamp},v1={sig}")  # no raise
    with pytest.raises(WebhookSignatureError):
        billing_router.verify_stripe_signature(body, f"t={timestamp},v1={'0' * 64}")
    with pytest.raises(WebhookSignatureError, match="tolerance"):
        old = str(int(time.time()) - 4000)
        old_sig = hmac.new(
            STRIPE_SECRET.encode(), f"{old}.".encode() + body, hashlib.sha256
        ).hexdigest()
        billing_router.verify_stripe_signature(body, f"t={old},v1={old_sig}")


def test_razorpay_signature_verifier(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.webhooks import billing_router

    monkeypatch.setattr(billing_router, "settings", _patched_settings())
    body = b'{"event": "subscription.charged"}'
    sig = hmac.new(RAZORPAY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    billing_router.verify_razorpay_signature(body, sig)  # valid → no raise
    with pytest.raises(WebhookSignatureError):
        billing_router.verify_razorpay_signature(body, "0" * 64)


def test_unconfigured_secret_rejects_instead_of_accepting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No secret configured must mean REJECT everything, never accept."""
    from app.modules.webhooks import meta_router

    monkeypatch.setattr(meta_router, "settings", _patched_settings(meta_app_secret=""))
    with pytest.raises(WebhookSignatureError):
        meta_router.verify_meta_signature(b"{}", _meta_signature(b"{}", "anything"))


# ---------------------------------------------------------------------------
# Facebook comment two-action handler (DoD)
# ---------------------------------------------------------------------------


def test_facebook_comment_triggers_public_reply_and_dm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD: one Graph API comment-reply call AND one Messenger DM call."""
    import httpx

    import app.db.base as db_base
    from app.modules.credentials.service import DecryptedCredential
    from app.worker import message_worker

    calls: list[str] = []

    class _FakeAsyncClient:
        def __init__(self, **_k: object) -> None: ...

        async def __aenter__(self) -> "_FakeAsyncClient":
            return self

        async def __aexit__(self, *_a: object) -> None: ...

        async def post(self, url: str, **_k: object) -> httpx.Response:
            calls.append(url)
            return httpx.Response(200, json={"id": "1"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(message_worker.httpx, "AsyncClient", _FakeAsyncClient)

    session = SimpleNamespace()

    @asynccontextmanager
    async def _fake_worker_session():  # noqa: ANN202
        yield session

    @asynccontextmanager
    async def _fake_scope(*_a: object, **_k: object):  # noqa: ANN202
        yield session

    async def _fake_resolve(*_a: object, **_k: object) -> uuid.UUID:
        return TENANT_ID

    async def _fake_upsert(*_a: object, **_k: object) -> uuid.UUID:
        return uuid.uuid4()

    async def _fake_save(*_a: object, **_k: object) -> None: ...

    async def _fake_reply_text(*_a: object, **_k: object) -> str:
        return "Thanks for reaching out! We've sent you a message 👋"

    async def _fake_finish(*_a: object, **_k: object) -> None: ...

    async def _fake_intent(*_a: object, **_k: object) -> object:
        return SimpleNamespace(
            intent="enquiry",
            confidence=0.9,
            is_urgent=False,
            requires_human=False,
            service_interest=None,
        )

    async def _fake_credential(*_a: object, **_k: object) -> DecryptedCredential:
        return DecryptedCredential(
            service="meta", fields={"access_token": "tok", "page_id": "page9"}
        )

    session.commit = _fake_save  # type: ignore[attr-defined]
    monkeypatch.setattr(message_worker, "worker_session", _fake_worker_session)
    monkeypatch.setattr(db_base, "with_tenant_scope", _fake_scope)
    monkeypatch.setattr(message_worker, "_resolve_tenant", _fake_resolve)
    monkeypatch.setattr(message_worker, "_upsert_lead", _fake_upsert)
    monkeypatch.setattr(message_worker, "_save_message", _fake_save)
    monkeypatch.setattr(message_worker, "_comment_reply_text", _fake_reply_text)
    monkeypatch.setattr(message_worker, "_finish_event", _fake_finish)
    monkeypatch.setattr(message_worker, "_notify_owner", lambda *_a, **_k: None)

    from app.modules.ai import intent_classification_service
    from app.modules.credentials import service as credential_service

    monkeypatch.setattr(intent_classification_service, "classify_intent", _fake_intent)
    monkeypatch.setattr(credential_service, "get_decrypted_credential", _fake_credential)

    enqueued: list[dict] = []
    monkeypatch.setattr(message_worker.generate_ai_response, "delay", lambda p: enqueued.append(p))

    message_worker.process_facebook_comment.run(
        {
            "external_id": "page9",
            "comment_id": "cmt_1",
            "commenter_psid": "psid_7",
            "commenter_name": "Asha",
            "text": "How much for bridal makeup?",
            "event_id": str(uuid.uuid4()),
        }
    )

    assert len(calls) == 2
    assert any("/cmt_1/comments" in url for url in calls)  # public reply
    assert any("/page9/messages" in url for url in calls)  # Messenger DM
    assert len(enqueued) == 1  # AI conversation pipeline started

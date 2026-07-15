"""Razorpay and Stripe webhook receivers.

Signature verification runs FIRST, over raw bytes, with constant-time
comparison — same discipline as the Meta receiver. After verification:
dedup claim → enqueue the billing Celery task → HTTP 200. The provider name
travels WITH the task so a Razorpay event can never be processed by Stripe
handling logic.
"""

import hashlib
import hmac
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import WebhookSignatureError
from app.db.base import get_session
from app.modules.webhooks.service import claim_webhook_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

DbSession = Annotated[AsyncSession, Depends(get_session)]

STRIPE_TIMESTAMP_TOLERANCE_S = 300


def verify_razorpay_signature(raw_body: bytes, signature_header: str) -> None:
    """HMAC-SHA256 of the raw body with the webhook secret (Razorpay docs)."""
    if not settings.razorpay_webhook_secret:
        raise WebhookSignatureError("Razorpay webhook secret is not configured")
    expected = hmac.new(
        settings.razorpay_webhook_secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise WebhookSignatureError("Invalid Razorpay webhook signature")


def verify_stripe_signature(raw_body: bytes, signature_header: str) -> None:
    """Stripe scheme: header `t=<ts>,v1=<sig>`; sig = HMAC-SHA256(f"{t}.{body}")."""
    if not settings.stripe_webhook_secret:
        raise WebhookSignatureError("Stripe webhook secret is not configured")
    parts = dict(item.split("=", 1) for item in signature_header.split(",") if "=" in item)
    timestamp = parts.get("t", "")
    provided = parts.get("v1", "")
    if not timestamp or not provided:
        raise WebhookSignatureError("Malformed Stripe signature header")
    if abs(time.time() - float(timestamp)) > STRIPE_TIMESTAMP_TOLERANCE_S:
        raise WebhookSignatureError("Stripe webhook timestamp outside tolerance")
    signed_payload = f"{timestamp}.".encode() + raw_body
    expected = hmac.new(
        settings.stripe_webhook_secret.encode(), signed_payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, provided):
        raise WebhookSignatureError("Invalid Stripe webhook signature")


@router.post("/razorpay", summary="Razorpay billing events")
async def receive_razorpay_event(request: Request, session: DbSession) -> dict[str, str]:
    raw_body = await request.body()
    verify_razorpay_signature(raw_body, request.headers.get("X-Razorpay-Signature", ""))

    payload = await request.json()
    event_type = str(payload.get("event", "unknown"))
    event_key = (
        request.headers.get("X-Razorpay-Event-Id")
        or f"razorpay:{event_type}:{payload.get('created_at', '')}"
    )

    event_id = await claim_webhook_event(
        session,
        platform_event_id=event_key,
        platform="razorpay",
        event_type=event_type,
        payload=payload,
    )
    if event_id is not None:
        from app.worker.billing_worker import process_billing_event

        process_billing_event.delay(
            {
                "provider": "razorpay",
                "event_type": event_type,
                "event_id": str(event_id),
                "payload": payload,
            }
        )
    return {"status": "received"}


@router.post("/stripe", summary="Stripe billing events")
async def receive_stripe_event(request: Request, session: DbSession) -> dict[str, str]:
    raw_body = await request.body()
    verify_stripe_signature(raw_body, request.headers.get("Stripe-Signature", ""))

    payload = await request.json()
    event_type = str(payload.get("type", "unknown"))
    event_key = str(payload.get("id", ""))

    event_id = await claim_webhook_event(
        session,
        platform_event_id=event_key,
        platform="stripe",
        event_type=event_type,
        payload=payload,
    )
    if event_id is not None:
        from app.worker.billing_worker import process_billing_event

        process_billing_event.delay(
            {
                "provider": "stripe",
                "event_type": event_type,
                "event_id": str(event_id),
                "payload": payload,
            }
        )
    return {"status": "received"}

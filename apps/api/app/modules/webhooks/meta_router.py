"""Meta webhook receiver — the most security-critical endpoint in the app.

It is PUBLIC (no auth possible: Meta calls it) and receives all Facebook,
Instagram, and WhatsApp events. Defence order is fixed:

1. HMAC-SHA256 signature verification over the RAW body bytes, compared
   with hmac.compare_digest (constant-time — `==` leaks timing). This runs
   BEFORE json parsing: parsed-then-verified code paths invite bypasses.
2. Deduplication claim against webhook_events (insert-before-process).
3. Enqueue the Celery task and return 200 — Meta's deadline is 200ms; ALL
   real work happens in workers.

The GET handler answers Meta's one-time subscription verification handshake.
"""

import hashlib
import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import WebhookSignatureError
from app.db.base import get_session
from app.modules.webhooks.service import claim_webhook_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

DbSession = Annotated[AsyncSession, Depends(get_session)]


def verify_meta_signature(raw_body: bytes, signature_header: str) -> None:
    """Constant-time HMAC-SHA256 verification of the raw request body."""
    if not settings.meta_app_secret:
        raise WebhookSignatureError("Meta webhook secret is not configured")
    expected = (
        "sha256="
        + hmac.new(settings.meta_app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(expected, signature_header):
        raise WebhookSignatureError("Invalid Meta webhook signature")


@router.get("/meta", summary="Meta subscription verification handshake")
async def verify_subscription(
    hub_mode: Annotated[str, Query(alias="hub.mode")] = "",
    hub_verify_token: Annotated[str, Query(alias="hub.verify_token")] = "",
    hub_challenge: Annotated[str, Query(alias="hub.challenge")] = "",
) -> Response:
    if hub_mode == "subscribe" and hmac.compare_digest(
        hub_verify_token, settings.meta_webhook_verify_token or "\x00unset"
    ):
        return Response(content=hub_challenge, media_type="text/plain")
    raise WebhookSignatureError("Meta subscription verification failed")


@router.post("/meta", summary="Meta event receiver (Facebook/Instagram/WhatsApp)")
async def receive_meta_event(request: Request, session: DbSession) -> dict[str, str]:
    # ── 1. Signature FIRST, over raw bytes, before any parsing ──
    raw_body = await request.body()
    verify_meta_signature(raw_body, request.headers.get("X-Hub-Signature-256", ""))

    payload = await request.json()
    object_type = str(payload.get("object", ""))

    # ── 2. Dedup + 3. enqueue per entry; heavy work belongs to Celery ──
    for entry in payload.get("entry", []):
        entry_id = str(entry.get("id", ""))
        event_key = f"meta:{object_type}:{entry_id}:{entry.get('time', '')}"
        event_id = await claim_webhook_event(
            session,
            platform_event_id=event_key,
            platform="meta",
            event_type=object_type,
            payload={"object": object_type, "entry": entry},
        )
        if event_id is None:
            continue  # duplicate delivery — already claimed
        _route_entry(object_type, entry_id, entry, str(event_id))

    return {"status": "received"}


def _items(container: dict[str, object], key: str) -> list[dict[str, object]]:
    """Typed access into Meta's loosely-shaped payloads: list of dicts or []."""
    raw = container.get(key)
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _child(container: dict[str, object], key: str) -> dict[str, object]:
    value = container.get(key)
    return value if isinstance(value, dict) else {}


def _route_entry(
    object_type: str, external_id: str, entry: dict[str, object], event_id: str
) -> None:
    """Fan the entry out to the right Celery pipeline based on `object`."""
    from app.worker.message_worker import process_facebook_comment, process_incoming_message

    if object_type == "whatsapp_business_account":
        for change in _items(entry, "changes"):
            value = _child(change, "value")
            for message in _items(value, "messages"):
                process_incoming_message.delay(
                    {
                        "platform": "whatsapp",
                        "external_id": str(
                            _child(value, "metadata").get("phone_number_id", external_id)
                        ),
                        "sender_id": str(message.get("from", "")),
                        "sender_name": _whatsapp_sender_name(value),
                        "text": str(_child(message, "text").get("body", "")),
                        "message_id": str(message.get("id", "")),
                        "event_id": event_id,
                    }
                )
    elif object_type == "page":
        for messaging in _items(entry, "messaging"):
            if "message" not in messaging:
                continue
            process_incoming_message.delay(
                {
                    "platform": "meta",
                    "external_id": external_id,
                    "sender_id": str(_child(messaging, "sender").get("id", "")),
                    "sender_name": "",
                    "text": str(_child(messaging, "message").get("text", "")),
                    "message_id": str(_child(messaging, "message").get("mid", "")),
                    "event_id": event_id,
                }
            )
        for change in _items(entry, "changes"):
            if change.get("field") != "feed":
                continue
            value = _child(change, "value")
            if value.get("item") == "comment" and value.get("verb") == "add":
                process_facebook_comment.delay(
                    {
                        "external_id": external_id,
                        "comment_id": str(value.get("comment_id", "")),
                        "commenter_psid": str(_child(value, "from").get("id", "")),
                        "commenter_name": str(_child(value, "from").get("name", "")),
                        "text": str(value.get("message", "")),
                        "event_id": event_id,
                    }
                )
    elif object_type == "instagram":
        for messaging in _items(entry, "messaging"):
            if "message" not in messaging:
                continue
            process_incoming_message.delay(
                {
                    "platform": "instagram",
                    "external_id": external_id,
                    "sender_id": str(_child(messaging, "sender").get("id", "")),
                    "sender_name": "",
                    "text": str(_child(messaging, "message").get("text", "")),
                    "message_id": str(_child(messaging, "message").get("mid", "")),
                    "event_id": event_id,
                }
            )
    else:
        logger.info("unhandled meta object type", extra={"object": object_type})


def _whatsapp_sender_name(value: dict[str, object]) -> str:
    contacts = value.get("contacts") or []
    if isinstance(contacts, list) and contacts:
        profile = contacts[0].get("profile", {}) if isinstance(contacts[0], dict) else {}
        return str(profile.get("name", ""))
    return ""

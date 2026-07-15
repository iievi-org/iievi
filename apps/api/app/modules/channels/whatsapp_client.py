"""WhatsApp Cloud API client.

Two send paths with ONE hard rule between them:
- send_session_message — free-form text, valid ONLY inside the 24-hour
  window opened by the lead's last inbound message
- send_template_message — pre-approved template, valid at any time

Before any free-form send the caller's lead is checked: if
lead.last_inbound_at is older than 24 hours the send raises
WhatsAppSessionExpiredError — the caller must send a template first to
re-open the window. Sending free-form outside the window is a hard Meta
policy violation that gets the business number banned.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.core.circuit import get_circuit
from app.core.exceptions import ExternalAPIError, WhatsAppSessionExpiredError
from app.modules.credentials.service import DecryptedCredential
from app.modules.posts.publishers.base import HTTP_TIMEOUT_S, logged_request

logger = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v20.0"
SESSION_WINDOW = timedelta(hours=24)


def session_window_open(last_inbound_at: datetime | None) -> bool:
    """True while the lead's 24-hour session window is open."""
    if last_inbound_at is None:
        return False
    reference = last_inbound_at if last_inbound_at.tzinfo else last_inbound_at.replace(tzinfo=UTC)
    return datetime.now(UTC) - reference < SESSION_WINDOW


def _log_delivery(
    *,
    lead_id: uuid.UUID | str | None,
    tenant_id: uuid.UUID | str | None,
    message_type: str,
    status: str,
) -> None:
    logger.info(
        "whatsapp delivery",
        extra={
            "lead_id": str(lead_id) if lead_id else "",
            "tenant_id": str(tenant_id) if tenant_id else "",
            "message_type": message_type,
            "delivery_status": status,
        },
    )


async def _send(
    credential: DecryptedCredential,
    body: dict[str, Any],
    *,
    message_type: str,
    lead_id: uuid.UUID | str | None,
    tenant_id: uuid.UUID | str | None,
) -> str:
    phone_number_id = credential.fields["phone_number_id"]
    token = credential.fields["access_token"]

    async def _run() -> str:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S) as client:
            response = await logged_request(
                client,
                "whatsapp",
                "POST",
                f"{GRAPH}/{phone_number_id}/messages",
                tenant_id=tenant_id,
                headers={"Authorization": f"Bearer {token}"},
                json=body,
            )
            if response.status_code != 200:
                _log_delivery(
                    lead_id=lead_id,
                    tenant_id=tenant_id,
                    message_type=message_type,
                    status="failed",
                )
                raise ExternalAPIError(
                    "WhatsApp send failed",
                    details={"status": response.status_code},
                )
            message_id = str(response.json()["messages"][0]["id"])
            _log_delivery(
                lead_id=lead_id,
                tenant_id=tenant_id,
                message_type=message_type,
                status="sent",
            )
            return message_id

    return await get_circuit("whatsapp").call(_run)


async def send_session_message(
    phone: str,
    text: str,
    credential: DecryptedCredential,
    *,
    last_inbound_at: datetime | None,
    lead_id: uuid.UUID | str | None = None,
    tenant_id: uuid.UUID | str | None = None,
) -> str:
    """Free-form message — ONLY valid inside the 24-hour session window."""
    if not session_window_open(last_inbound_at):
        raise WhatsAppSessionExpiredError(
            "The 24-hour WhatsApp session window is closed — send a template message to re-open it",
            details={"phone": phone[-4:].rjust(len(phone), "*")},
        )
    body = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": text},
    }
    return await _send(
        credential, body, message_type="session", lead_id=lead_id, tenant_id=tenant_id
    )


async def send_template_message(
    phone: str,
    template_name: str,
    language: str,
    parameters: list[str],
    credential: DecryptedCredential,
    *,
    lead_id: uuid.UUID | str | None = None,
    tenant_id: uuid.UUID | str | None = None,
) -> str:
    """Pre-approved template message — valid at any time."""
    components = (
        [
            {
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in parameters],
            }
        ]
        if parameters
        else []
    )
    body = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": components,
        },
    }
    return await _send(
        credential, body, message_type="template", lead_id=lead_id, tenant_id=tenant_id
    )

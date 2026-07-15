"""Channel-agnostic outbound delivery — shared by the AI reply and outreach paths.

Routes a plain-text message to the lead's platform: WhatsApp (a free-form
session message, valid only inside the lead's 24-hour window) or Meta/Instagram
(a Messenger DM). Returns False when the message could not be delivered — no
credential, a closed WhatsApp window, or an unsupported platform — so the caller
can escalate to the owner instead of failing silently.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

import httpx

from app.core.circuit import get_circuit
from app.core.exceptions import ExternalAPIError, WhatsAppSessionExpiredError

logger = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v20.0"

# Lead platform -> the stored credential service used to deliver on it.
_DELIVERY_SERVICE: dict[str, str] = {
    "whatsapp": "whatsapp",
    "meta": "meta",
    "instagram": "meta",
}


def delivery_service_for(platform: str) -> str | None:
    """The credential service name needed to deliver on this platform, if any."""
    return _DELIVERY_SERVICE.get(platform)


async def deliver_message(
    *,
    platform: str,
    platform_id: str,
    text: str,
    credential: Any | None,  # noqa: ANN401 — DecryptedCredential; kept loose for the worker path
    lead_id: uuid.UUID | str,
    tenant_id: uuid.UUID | str,
    last_inbound_at: datetime | None = None,
) -> bool:
    """Send ``text`` to the lead on their channel. Returns False if it couldn't go out."""
    if credential is None:
        logger.warning(
            "no delivery credential", extra={"platform": platform, "tenant_id": str(tenant_id)}
        )
        return False
    try:
        if platform == "whatsapp":
            from app.modules.channels.whatsapp_client import send_session_message

            await send_session_message(
                platform_id,
                text,
                credential,
                last_inbound_at=last_inbound_at,
                lead_id=lead_id,
                tenant_id=tenant_id,
            )
            return True
        if platform in ("meta", "instagram"):
            await _send_meta_dm(platform_id, text, credential, tenant_id)
            return True
        logger.info("no delivery channel for platform", extra={"platform": platform})
        return False
    except (WhatsAppSessionExpiredError, ExternalAPIError):
        logger.error(
            "message delivery failed", extra={"platform": platform, "lead_id": str(lead_id)}
        )
        return False


async def _send_meta_dm(
    recipient_id: str,
    text_body: str,
    credential: Any,  # noqa: ANN401
    tenant_id: uuid.UUID | str,
) -> None:
    token = credential.fields["access_token"]
    page_id = credential.fields["page_id"]

    async def _run() -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{GRAPH}/{page_id}/messages",
                params={"access_token": token},
                json={
                    "recipient": {"id": recipient_id},
                    "message": {"text": text_body},
                    "messaging_type": "RESPONSE",
                },
            )
            if response.status_code != 200:
                raise ExternalAPIError(
                    "Meta DM send failed", details={"status": response.status_code}
                )

    await get_circuit("meta").call(_run)

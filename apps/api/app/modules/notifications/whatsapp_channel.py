"""Platform-owned WhatsApp notification channel — Prompt 7 Step 6.

Distinct from a tenant's lead-facing WhatsApp: this sends OWNER notifications
(e.g. handoff summaries) from IIEVI's own WhatsApp number, configured via
``PLATFORM_WHATSAPP_TOKEN`` / ``PLATFORM_WHATSAPP_PHONE_ID``. A missing config or
a send failure is logged and swallowed — owner WhatsApp is a best-effort channel
that must never break the flow that triggered it.
"""

import logging

import httpx

from app.core.circuit import get_circuit
from app.core.config import settings

logger = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v20.0"


def is_configured() -> bool:
    """True when the platform WhatsApp number is set up."""
    return bool(settings.platform_whatsapp_token and settings.platform_whatsapp_phone_id)


async def send_owner_whatsapp(to_phone: str, message: str) -> bool:
    """Send a plain-text WhatsApp notification to a business owner. Returns
    False (and logs) if the channel isn't configured or the send fails."""
    if not is_configured():
        logger.info("platform whatsapp not configured; skipping owner notification")
        return False

    async def _run() -> bool:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{GRAPH}/{settings.platform_whatsapp_phone_id}/messages",
                headers={"Authorization": f"Bearer {settings.platform_whatsapp_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to_phone,
                    "type": "text",
                    "text": {"body": message},
                },
            )
            return response.status_code == 200

    try:
        return await get_circuit("platform_whatsapp").call(_run)
    except Exception:  # noqa: BLE001 — best-effort; never break the caller
        logger.warning("owner whatsapp notification failed")
        return False

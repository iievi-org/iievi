"""Incoming-message intent classification.

Runs on the PLATFORM's own small AI budget (Gemini Flash-Lite via
app.core.ai) because classification happens BEFORE tenant context is fully
established — the message text is the only input.

Intent routing contract (enforced by the message pipeline):
- enquiry, confidence ≥ 0.7  → create lead + AI response
- enquiry, confidence < 0.7  → create lead flagged for manual review, NO AI
- complaint                  → manual_mode=True immediately, notify owner
- spam                       → discarded
- is_urgent (any intent)     → immediate owner notification
"""

import json
import logging
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.core import ai
from app.core.exceptions import AIGenerationError

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7


class IntentClassification(BaseModel):
    intent: Literal["enquiry", "compliment", "complaint", "spam", "other"]
    service_interest: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    is_urgent: bool = False
    requires_human: bool = False


_SYSTEM = """You classify ONE incoming social media / WhatsApp message sent \
to a small service business. Respond with ONLY valid JSON, no prose:

{"intent": "enquiry|compliment|complaint|spam|other",
 "service_interest": "<service mentioned, or null>",
 "confidence": <0.0-1.0>,
 "is_urgent": <true if the message uses emergency/urgent language>,
 "requires_human": <true if the sender sounds angry or is complaining>}

Rules:
- "enquiry" = asking about services, prices, availability, or booking.
- "complaint" = dissatisfaction with delivered work or service.
- "spam" = promotions, link farms, crypto, unrelated solicitations.
- confidence reflects how sure you are of the intent label alone.
"""


async def classify_intent(message_text: str) -> IntentClassification:
    """Classify one message; malformed model output degrades to manual review."""
    raw = await ai.complete(
        system=_SYSTEM,
        user_message=message_text[:4000],
        model=ai.FLASH_LITE_MODEL,
        max_tokens=256,
        trace_name="intent-classification",
    )
    try:
        return IntentClassification.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("intent classification produced invalid output", extra={"raw": raw[:200]})
        raise AIGenerationError("Intent classification failed") from exc

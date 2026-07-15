"""Intent signal detection — Prompt 7 Step 4.

A tiny, deterministic classifier that reads ONLY the last three turns of a
conversation (not the full history) and extracts four booleans the state
machine acts on. Runs on the tenant's own key at temperature 0.0 for maximum
consistency, and every call is traced to LangFuse via ``traced_ai_call``.

Malformed model output never crashes the pipeline: a parse failure degrades to
``IntentSignals()`` (all False), i.e. "no signal, stay in the current state".
"""

import json
import logging
import uuid
from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from app.core.ai import FLASH_LITE_MODEL
from app.core.exceptions import AIGenerationError, ExternalAPIError
from app.modules.ai.langfuse_client import traced_ai_call

logger = logging.getLogger(__name__)

# Only the last three turns are considered — enough for intent, cheap and fast.
_TURN_WINDOW = 3
_MAX_TOKENS = 120

_SYSTEM_PROMPT = (
    "You extract intent signals from the recent turns of a sales chat between a "
    "business Assistant and a Customer. Output a JSON object with EXACTLY these "
    "four boolean keys and nothing else:\n"
    '- "lead_ready": the customer wants to book/buy/schedule NOW '
    '(e.g. "let\'s do it", "how do I pay", "book me in", "yes please go ahead").\n'
    '- "requested_human": the customer asked to speak to a person/owner/team, '
    'or is clearly frustrated with the bot (e.g. "talk to a human", "call me", '
    '"is anyone real there", "stop the bot").\n'
    '- "objection_expressed": the customer raised a concern or hesitation about '
    'price, timing, trust, or fit (e.g. "too expensive", "not sure", "maybe later").\n'
    '- "all_questions_answered": the customer has given enough to qualify them — '
    "their need, rough scope/timing, and intent to proceed are all reasonably clear.\n"
    "Return ONLY the JSON object. No prose, no markdown, no code fences.\n"
    'Example: {"lead_ready": false, "requested_human": false, '
    '"objection_expressed": true, "all_questions_answered": false}'
)


class IntentSignals(BaseModel):
    """The four booleans the conversation state machine consumes.

    Extra keys from the model are ignored so a chatty response still parses;
    every field defaults False so ``IntentSignals()`` is the safe fallback.
    """

    model_config = {"extra": "ignore"}

    lead_ready: bool = False
    requested_human: bool = False
    objection_expressed: bool = False
    all_questions_answered: bool = False


def _format_turns(turns: Sequence[dict[str, str]]) -> str:
    """Render the last few turns as 'Customer:'/'Assistant:' lines."""
    lines: list[str] = []
    for turn in list(turns)[-_TURN_WINDOW:]:
        role = str(turn.get("role", "lead")).lower()
        content = str(turn.get("content", "")).strip()
        if not content:
            continue
        speaker = "Customer" if role in ("lead", "user", "customer") else "Assistant"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


def _extract_json_object(raw: str) -> str:
    """Slice the outermost {...} so wrapping prose or code fences don't break parsing."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return raw
    return raw[start : end + 1]


async def detect_intent(
    last_three_turns: Sequence[dict[str, str]],
    tenant_id: uuid.UUID,
    *,
    api_key: str,
) -> IntentSignals:
    """Classify the last three turns into intent signals.

    Never raises: a provider error or malformed output returns the all-False
    default so the conversation simply stays in its current state.
    """
    conversation = _format_turns(last_three_turns)
    if not conversation:
        return IntentSignals()

    try:
        result = await traced_ai_call(
            api_key=api_key,
            system=_SYSTEM_PROMPT,
            user_message=f"Recent turns:\n{conversation}",
            model=FLASH_LITE_MODEL,
            call_type="intent-detection",
            tenant_id=tenant_id,
            temperature=0.0,
            max_tokens=_MAX_TOKENS,
        )
    except (AIGenerationError, ExternalAPIError):
        logger.warning("intent detection call failed", extra={"tenant_id": str(tenant_id)})
        return IntentSignals()

    try:
        payload = json.loads(_extract_json_object(result.text))
        return IntentSignals.model_validate(payload)
    except (json.JSONDecodeError, ValidationError, TypeError):
        logger.warning(
            "intent detection produced invalid output",
            extra={"tenant_id": str(tenant_id), "raw": result.text[:200]},
        )
        return IntentSignals()

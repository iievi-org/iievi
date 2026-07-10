"""LangFuse-traced Gemini call — the ONE gateway for tenant-facing AI.

Every tenant-facing AI call in the platform goes through traced_ai_call:
- runs on the TENANT's own Gemini key (passed explicitly by the caller,
  fetched via the credential service)
- passes through the shared `gemini` circuit breaker
- records a LangFuse generation: truncated system prompt, input, output,
  token counts, latency, model, call type, and the tenant_id as a tag
- computes the estimated USD cost from token counts and enforces the daily
  per-tenant budget alarm (protects against a runaway/compromised key)

Platform-side calls (onboarding, intent classification before a tenant is
identified) keep using app.core.ai on the platform key.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from google import genai
from google.genai import types

from app.core.ai import FLASH_LITE_MODEL, FLASH_MODEL
from app.core.circuit import get_circuit
from app.core.config import settings
from app.core.exceptions import AIGenerationError, ExternalAPIError
from app.core.ops import notify_ops
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

TRACE_SYSTEM_PROMPT_MAX_CHARS = 5000
BUDGET_KEY_TTL_S = 2 * 24 * 3600  # keep yesterday's counter around for ops queries

# USD per one million tokens (input, output). Unknown models cost 0 — the
# trace still records token counts so pricing gaps are visible in LangFuse.
MODEL_PRICING_PER_MTOK: dict[str, tuple[float, float]] = {
    FLASH_MODEL: (0.30, 2.50),
    FLASH_LITE_MODEL: (0.10, 0.40),
    "gemini-2.5-flash-image": (0.30, 30.00),
}


@dataclass(frozen=True)
class AICallResult:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    model: str
    estimated_cost_usd: float


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_rate, output_rate = MODEL_PRICING_PER_MTOK.get(model, (0.0, 0.0))
    return (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000


async def track_daily_spend(tenant_id: uuid.UUID, cost_usd: float) -> float:
    """Accumulate today's estimated spend; alarm once it crosses the budget."""
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    key = f"ai_cost:{tenant_id}:{day}"
    redis = get_redis()
    total = float(await redis.incrbyfloat(key, cost_usd))
    await redis.expire(key, BUDGET_KEY_TTL_S)
    if total > settings.ai_daily_budget_usd:
        logger.warning(
            "tenant exceeded daily AI budget",
            extra={"tenant_id": str(tenant_id), "spend_usd": round(total, 4)},
        )
        notify_ops(
            f"tenant {tenant_id} exceeded the ${settings.ai_daily_budget_usd:.2f} "
            f"daily AI budget (est. ${total:.2f}) — possible runaway usage"
        )
    return total


async def traced_ai_call(
    *,
    api_key: str,
    system: str,
    user_message: str,
    model: str = FLASH_MODEL,
    call_type: str = "completion",
    tenant_id: uuid.UUID | None = None,
    temperature: float | None = None,
    max_tokens: int = 1024,
) -> AICallResult:
    """One traced, circuit-protected, budget-metered Gemini completion."""
    started = time.perf_counter()

    async def _raw() -> object:
        client = genai.Client(api_key=api_key)
        try:
            return await client.aio.models.generate_content(
                model=model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
        except Exception as exc:  # noqa: BLE001 — normalise SDK errors at the boundary
            raise ExternalAPIError("Gemini call failed") from exc

    response = await get_circuit("gemini").call(_raw)
    latency_ms = int((time.perf_counter() - started) * 1000)

    text = getattr(response, "text", None)
    if not text:
        raise AIGenerationError("AI response contained no text")

    usage = getattr(response, "usage_metadata", None)
    input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
    output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
    cost = estimate_cost_usd(model, input_tokens, output_tokens)

    result = AICallResult(
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        model=model,
        estimated_cost_usd=cost,
    )

    if tenant_id is not None:
        await track_daily_spend(tenant_id, cost)

    _record_trace(
        system=system,
        user_message=user_message,
        result=result,
        call_type=call_type,
        tenant_id=tenant_id,
    )
    return result


def _record_trace(
    *,
    system: str,
    user_message: str,
    result: AICallResult,
    call_type: str,
    tenant_id: uuid.UUID | None,
) -> None:
    """Ship the generation to LangFuse; silently disabled without keys."""
    if not settings.langfuse_public_key:
        return
    try:
        from langfuse import Langfuse

        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        with client.start_as_current_observation(
            name=call_type, as_type="generation"
        ) as generation:
            generation.update(
                model=result.model,
                input={
                    "system": system[:TRACE_SYSTEM_PROMPT_MAX_CHARS],
                    "user": user_message,
                },
                output=result.text,
                usage_details={"input": result.input_tokens, "output": result.output_tokens},
                metadata={
                    "call_type": call_type,
                    "latency_ms": result.latency_ms,
                    "estimated_cost_usd": result.estimated_cost_usd,
                    # tenant tag — LangFuse metadata is filterable per-trace
                    "tenant_id": str(tenant_id) if tenant_id else "",
                },
            )
    except Exception:  # noqa: BLE001 — observability must never break the product path
        logger.exception("langfuse trace recording failed")

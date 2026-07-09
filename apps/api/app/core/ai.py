"""LangFuse-traced Claude wrapper for PLATFORM-side AI calls.

Used by onboarding extraction (runs on the platform's Anthropic key, since
the prospect has no account yet). Tenant-facing AI in later phases loads the
tenant's OWN key via the credential service and passes it explicitly.

Model policy (setup spec): Claude Sonnet 4 for generation/extraction,
Claude Haiku 3.5 for conversations.
"""

import logging

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.exceptions import AIGenerationError

logger = logging.getLogger(__name__)

SONNET_MODEL = "claude-sonnet-4-20250514"
HAIKU_MODEL = "claude-haiku-3-5-20251001"

_client: AsyncAnthropic | None = None
_langfuse_ready = False


def _get_client() -> AsyncAnthropic:
    global _client  # noqa: PLW0603 — process-wide lazy singleton
    if _client is None:
        if not settings.anthropic_api_key:
            raise AIGenerationError(
                "Platform ANTHROPIC_API_KEY is not configured — "
                "onboarding extraction is unavailable"
            )
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _init_langfuse() -> None:
    """Initialise LangFuse once; tracing silently disables without keys."""
    global _langfuse_ready  # noqa: PLW0603
    if _langfuse_ready or not settings.langfuse_public_key:
        return
    from langfuse import Langfuse

    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    _langfuse_ready = True


async def complete(
    *,
    system: str,
    user_message: str,
    model: str = SONNET_MODEL,
    max_tokens: int = 1024,
    trace_name: str = "platform-completion",
    session_id: str | None = None,
) -> str:
    """One traced completion; returns the text of the first content block."""
    _init_langfuse()
    client = _get_client()
    try:
        if _langfuse_ready:
            from langfuse import observe  # decorator API traces the call tree

            @observe(name=trace_name)
            async def _traced() -> str:
                return await _raw_call(client, system, user_message, model, max_tokens)

            return await _traced()
        return await _raw_call(client, system, user_message, model, max_tokens)
    except AIGenerationError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalise SDK errors at the boundary
        logger.error("anthropic call failed", extra={"trace": trace_name, "error": str(exc)})
        raise AIGenerationError("AI provider call failed") from exc


async def _raw_call(
    client: AsyncAnthropic, system: str, user_message: str, model: str, max_tokens: int
) -> str:
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    for block in response.content:
        if block.type == "text":
            return block.text
    raise AIGenerationError("AI response contained no text block")

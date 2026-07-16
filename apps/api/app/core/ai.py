"""LangFuse-traced Gemini wrapper for PLATFORM-side AI calls.

Used by onboarding extraction (runs on the platform's Gemini key, since
the prospect has no account yet). Tenant-facing AI in later phases loads the
tenant's OWN key via the credential service and passes it explicitly.

Model policy: Gemini 2.5 Flash for generation/extraction, Gemini 2.5
Flash-Lite for conversations, Gemini 2.5 Flash Image for image generation —
one GEMINI_API_KEY covers text AND images.
"""

import logging

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.exceptions import AIGenerationError

logger = logging.getLogger(__name__)

FLASH_MODEL = "gemini-2.5-flash"
FLASH_LITE_MODEL = "gemini-2.5-flash-lite"
IMAGE_MODEL = "gemini-2.5-flash-image"

_client: genai.Client | None = None
_langfuse_ready = False


def _get_client() -> genai.Client:
    global _client  # noqa: PLW0603 — process-wide lazy singleton
    if _client is None:
        if not settings.gemini_api_key:
            raise AIGenerationError(
                "Platform GEMINI_API_KEY is not configured — onboarding extraction is unavailable"
            )
        _client = genai.Client(api_key=settings.gemini_api_key)
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
    model: str = FLASH_MODEL,
    max_tokens: int = 1024,
    trace_name: str = "platform-completion",
    session_id: str | None = None,
) -> str:
    """One traced completion; returns the response text."""
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
        logger.error("gemini call failed", extra={"trace": trace_name, "error": str(exc)})
        raise AIGenerationError("AI provider call failed") from exc


async def generate_image(
    *,
    prompt: str,
    model: str = IMAGE_MODEL,
    trace_name: str = "platform-image",
) -> bytes:
    """One traced image generation; returns the raw image bytes (PNG)."""
    _init_langfuse()
    client = _get_client()
    try:
        if _langfuse_ready:
            from langfuse import observe

            @observe(name=trace_name)
            async def _traced() -> bytes:
                return await _raw_image_call(client, prompt, model)

            return await _traced()
        return await _raw_image_call(client, prompt, model)
    except AIGenerationError:
        raise
    except Exception as exc:  # noqa: BLE001 — normalise SDK errors at the boundary
        logger.error("gemini image call failed", extra={"trace": trace_name, "error": str(exc)})
        raise AIGenerationError("AI provider call failed") from exc


async def _raw_call(
    client: genai.Client, system: str, user_message: str, model: str, max_tokens: int
) -> str:
    response = await client.aio.models.generate_content(
        model=model,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    if response.text:
        return response.text
    raise AIGenerationError("AI response contained no text")


async def _raw_image_call(client: genai.Client, prompt: str, model: str) -> bytes:
    response = await client.aio.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for candidate in response.candidates or []:
        parts = candidate.content.parts if candidate.content else None
        for part in parts or []:
            if part.inline_data and part.inline_data.data:
                return part.inline_data.data
    raise AIGenerationError("AI response contained no image")

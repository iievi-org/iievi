"""Post copy generation — tenant-keyed, platform-aware, validated twice.

The model contract: return ONLY JSON matching PostCopyOutput. Output is
validated with Pydantic (plus per-platform caption length rules) BEFORE it
touches the database. A validation failure triggers exactly ONE retry with
the validation error included as an explicit correction instruction; a
second failure raises AIGenerationError — we never store unvalidated copy.
"""

import json
import logging
import uuid

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai import FLASH_MODEL
from app.core.exceptions import AIGenerationError
from app.modules.ai.context_service import assemble_tenant_context
from app.modules.ai.langfuse_client import traced_ai_call
from app.modules.credentials.service import get_decrypted_credential

logger = logging.getLogger(__name__)

GENERATION_TEMPERATURE = 0.7

# Platform-specific composition rules: (max caption chars, instructions)
PLATFORM_RULES: dict[str, tuple[int, str]] = {
    "instagram": (
        2200,
        "Write an Instagram caption: hook in the first line (it shows before "
        "the fold), short paragraphs, emotive but genuine. Include 5-10 "
        "relevant hashtags mixing niche and broad reach.",
    ),
    "facebook": (
        3000,
        "Write a conversational Facebook post that ENDS with a question to "
        "the audience to invite comments. 2-4 hashtags maximum.",
    ),
    "linkedin": (
        3000,
        "Write a professional LinkedIn post with an insight-led opening line "
        "(a lesson or observation, not a sales pitch). No emoji walls. "
        "3-5 professional hashtags.",
    ),
    "tiktok": (
        150,
        "Write a punchy TikTok caption UNDER 150 characters. High energy, "
        "direct. 2-4 trending-style hashtags.",
    ),
}


class PostCopyOutput(BaseModel):
    """Validated generation output — platform length rules applied separately."""

    model_config = {"extra": "forbid"}

    caption: str = Field(min_length=10)
    hashtags: list[str] = Field(default_factory=list, max_length=15)
    call_to_action: str = Field(min_length=3, max_length=280)
    # Passed verbatim to image generation as the content description
    image_description: str = Field(min_length=10, max_length=2000)
    template_style: str = Field(min_length=2, max_length=64)

    @field_validator("hashtags")
    @classmethod
    def _hash_prefixed(cls, v: list[str]) -> list[str]:
        bad = [h for h in v if not h.startswith("#")]
        if bad:
            msg = f"hashtags must start with '#': {bad}"
            raise ValueError(msg)
        return v


def validate_copy(platform: str, payload: dict[str, object]) -> PostCopyOutput:
    """Pydantic validation plus the platform's caption length ceiling."""
    output = PostCopyOutput.model_validate(payload)
    max_chars, _ = PLATFORM_RULES[platform]
    if len(output.caption) > max_chars:
        msg = f"caption is {len(output.caption)} chars; {platform} allows {max_chars}"
        raise ValueError(msg)
    return output


def _build_system_prompt(platform: str, context_summary: str) -> str:
    _, platform_instructions = PLATFORM_RULES[platform]
    schema = json.dumps(PostCopyOutput.model_json_schema(), indent=None)
    return f"""You write social media copy for this Indian service business:

{context_summary}

{platform_instructions}

Rules — no exceptions:
1. Talk ONLY about services this business actually offers (listed above).
   NEVER invent services, prices, offers, or claims.
2. Respond with ONLY valid JSON matching this schema, no prose, no markdown:
{schema}
3. image_description must describe a single promotional image for this post
   (subject, setting, mood) WITHOUT any embedded text or logos.
"""


def _summarise_context(context: object) -> str:
    """Compact profile summary for the system prompt."""
    ctx = context  # TenantAIContext
    parts = [
        f"Business: {ctx.business_name} ({ctx.category})",  # type: ignore[attr-defined]
        f"About: {ctx.description or 'n/a'}",  # type: ignore[attr-defined]
        f"Services: {json.dumps(ctx.services)[:1500]}",  # type: ignore[attr-defined]
        f"Audience: {json.dumps(ctx.target_audience)[:500]}",  # type: ignore[attr-defined]
        f"Tone: {ctx.tone or 'friendly, professional'}",  # type: ignore[attr-defined]
    ]
    return "\n".join(parts)


async def generate_post_copy(
    tenant_id: uuid.UUID,
    platform: str,
    topic: str,
    session: AsyncSession,
) -> PostCopyOutput:
    """Generate validated post copy on the tenant's own Gemini key."""
    if platform not in PLATFORM_RULES:
        msg = f"unsupported platform: {platform}"
        raise ValueError(msg)

    context = await assemble_tenant_context(tenant_id, session)
    credential = await get_decrypted_credential(tenant_id, "gemini", session)
    system = _build_system_prompt(platform, _summarise_context(context))

    user_message = f"Topic for this post: {topic}"
    last_error = ""
    for attempt in (1, 2):
        if attempt == 2:
            user_message = (
                f"Topic for this post: {topic}\n\n"
                f"Your previous response failed validation with this error:\n"
                f"{last_error}\n"
                f"Correct the output and respond with ONLY the fixed JSON."
            )
        result = await traced_ai_call(
            api_key=credential.fields["api_key"],
            system=system,
            user_message=user_message,
            model=FLASH_MODEL,
            call_type=f"post-copy-{platform}",
            tenant_id=tenant_id,
            temperature=GENERATION_TEMPERATURE,
            max_tokens=2048,
        )
        try:
            payload = json.loads(result.text)
            return validate_copy(platform, payload)
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = str(exc)[:1000]
            logger.warning(
                "post copy validation failed",
                extra={"tenant_id": str(tenant_id), "platform": platform, "attempt": attempt},
            )

    raise AIGenerationError(
        "Post copy generation failed validation twice",
        details={"platform": platform, "last_error": last_error[:500]},
    )

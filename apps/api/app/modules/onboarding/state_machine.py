"""Onboarding state machine — 12 stages, one message per turn.

Each stage defines: a question generator, a response processor (which may
call the Gemini extraction pipeline), and a completeness validator. A turn
either advances to the next stage, or returns a targeted clarification and
stays put. The final CONFIRM_AND_CREATE stage requires an authenticated
tenant and materialises the collected profile (done in the router, which has
the scoped session).
"""

import enum
import logging
from dataclasses import dataclass

from pydantic import BaseModel

from app.modules.onboarding import extraction_service
from app.modules.profiles.categories import CATEGORIES

logger = logging.getLogger(__name__)

MIN_FREE_TEXT = 3
MIN_OVERVIEW = 20


class OnboardingStage(enum.StrEnum):
    WELCOME = "welcome"
    CATEGORY_SELECT = "category_select"
    BUSINESS_INFO = "business_info"
    BUSINESS_OVERVIEW = "business_overview"
    TARGET_AUDIENCE = "target_audience"
    EXISTING_CUSTOMERS = "existing_customers"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    BRAND_IDENTITY = "brand_identity"
    CREATIVE_PREFERENCES = "creative_preferences"
    MARKETING_GOALS = "marketing_goals"
    LEAD_MANAGEMENT = "lead_management"
    CONFIRM_AND_CREATE = "confirm_and_create"


STAGE_ORDER: tuple[OnboardingStage, ...] = tuple(OnboardingStage)


def next_stage(stage: OnboardingStage) -> OnboardingStage | None:
    index = STAGE_ORDER.index(stage)
    return STAGE_ORDER[index + 1] if index + 1 < len(STAGE_ORDER) else None


class OnboardingTurnResponse(BaseModel):
    """What the chat frontend renders after each message."""

    stage: str
    reply: str
    advanced: bool
    completed: bool = False
    requires_auth: bool = False


@dataclass(frozen=True)
class TurnResult:
    updates: dict[str, object]
    complete: bool
    clarification: str | None = None


def _question_welcome(_data: dict[str, object]) -> str:
    return (
        "Welcome to IIEVI! I'll set up your AI growth engine in about ten "
        "minutes of questions. Ready to start? (just say yes, or ask me anything)"
    )


def _question_category(_data: dict[str, object]) -> str:
    options = ", ".join(f"{c.emoji} {c.display_name}" for c in list(CATEGORIES.values())[:8])
    return (
        f"What kind of business do you run? For example: {options}… or tell me in your own words."
    )


def _question_business_info(_data: dict[str, object]) -> str:
    return "What's your business name, and which city/areas do you serve?"


def _question_overview(_data: dict[str, object]) -> str:
    return (
        "Tell me about your services — what do you offer and roughly what do "
        "you charge? List as many as you like with price ranges."
    )


def _question_audience(_data: dict[str, object]) -> str:
    return "Who are your ideal customers? Think age group, area, what problem brings them to you."


def _question_existing(_data: dict[str, object]) -> str:
    return (
        "Tell me about your current customers — roughly how many do you serve "
        "a month, and how do they usually find you today?"
    )


def _question_competitors(_data: dict[str, object]) -> str:
    return "Which competitors do you keep an eye on, and what makes customers pick you over them?"


def _question_brand(_data: dict[str, object]) -> str:
    return (
        "Let's talk brand: what are your brand colours (or logo colours), and "
        "how would you describe your style — premium, friendly, bold, minimal?"
    )


def _question_creative(_data: dict[str, object]) -> str:
    return (
        "For your social posts: any preferences? (e.g. before/after photos, "
        "testimonials, offers, festive posts — and anything you do NOT want)"
    )


def _question_goals(_data: dict[str, object]) -> str:
    return (
        "What matters most in the next 3 months: more leads, more bookings, "
        "building your brand, or filling a quiet season? Any monthly target?"
    )


def _question_leads(_data: dict[str, object]) -> str:
    return (
        "When a new lead messages you, how fast can you respond, and when "
        "should the AI hand a conversation over to you personally?"
    )


def _question_confirm(data: dict[str, object]) -> str:
    business = data.get("business_info", {})
    name = business.get("raw", "your business") if isinstance(business, dict) else "your business"
    return (
        f"That's everything I need for {name}! Say 'confirm' and I'll create "
        "your complete profile. You can edit any of it later."
    )


async def _process_free_text(message: str, key: str, minimum: int = MIN_FREE_TEXT) -> TurnResult:
    text = message.strip()
    if len(text) < minimum:
        return TurnResult(
            updates={},
            complete=False,
            clarification="Could you give me a little more detail there?",
        )
    return TurnResult(updates={key: {"raw": text}}, complete=True)


async def _process_welcome(message: str, _data: dict[str, object]) -> TurnResult:
    return TurnResult(updates={"welcome": {"raw": message.strip()}}, complete=True)


async def _process_category(message: str, _data: dict[str, object]) -> TurnResult:
    lowered = message.lower()
    for key, config in CATEGORIES.items():
        if key.replace("_", " ") in lowered or config.display_name.lower() in lowered:
            return TurnResult(updates={"category": {"key": key}}, complete=True)
    # fuzzy single-word match ("plumber" → plumbing, "salon" → salon_beauty)
    for key in CATEGORIES:
        for fragment in key.split("_"):
            if len(fragment) > 3 and fragment in lowered:
                return TurnResult(updates={"category": {"key": key}}, complete=True)
    return TurnResult(
        updates={},
        complete=False,
        clarification=(
            "I couldn't match that to a category. Is it closest to: "
            + ", ".join(c.display_name for c in CATEGORIES.values())
            + "?"
        ),
    )


async def _process_services(message: str, data: dict[str, object]) -> TurnResult:
    token = str(data.get("__token", ""))
    outcome = await extraction_service.extract(
        kind="services", user_answer=message, session_token=token
    )
    if outcome.clarification:
        return TurnResult(updates={}, complete=False, clarification=outcome.clarification)
    return TurnResult(updates={"services": outcome.data or {}}, complete=True)


async def _process_audience(message: str, data: dict[str, object]) -> TurnResult:
    token = str(data.get("__token", ""))
    outcome = await extraction_service.extract(
        kind="target_audience", user_answer=message, session_token=token
    )
    if outcome.clarification:
        return TurnResult(updates={}, complete=False, clarification=outcome.clarification)
    return TurnResult(updates={"target_audience": outcome.data or {}}, complete=True)


async def _process_competitors(message: str, data: dict[str, object]) -> TurnResult:
    token = str(data.get("__token", ""))
    outcome = await extraction_service.extract(
        kind="competitors", user_answer=message, session_token=token
    )
    if outcome.clarification:
        return TurnResult(updates={}, complete=False, clarification=outcome.clarification)
    return TurnResult(updates={"competitors": outcome.data or {}}, complete=True)


@dataclass(frozen=True)
class StageSpec:
    question: object  # (data) -> str
    process: object  # async (message, data) -> TurnResult


async def _process_business_info(message: str, _d: dict[str, object]) -> TurnResult:
    return await _process_free_text(message, "business_info", minimum=MIN_FREE_TEXT)


async def _process_overview_stage(message: str, data: dict[str, object]) -> TurnResult:
    # Overview doubles as the services answer — run extraction on it.
    return await _process_services(message, data)


async def _process_existing(message: str, _d: dict[str, object]) -> TurnResult:
    return await _process_free_text(message, "existing_customers")


async def _process_brand(message: str, _d: dict[str, object]) -> TurnResult:
    return await _process_free_text(message, "brand_identity")


async def _process_creative(message: str, _d: dict[str, object]) -> TurnResult:
    return await _process_free_text(message, "creative_preferences")


async def _process_goals(message: str, _d: dict[str, object]) -> TurnResult:
    return await _process_free_text(message, "marketing_goals")


async def _process_leads(message: str, _d: dict[str, object]) -> TurnResult:
    return await _process_free_text(message, "lead_management")


async def _process_confirm(message: str, _d: dict[str, object]) -> TurnResult:
    if "confirm" not in message.lower():
        return TurnResult(
            updates={},
            complete=False,
            clarification="Say 'confirm' when you're ready, or tell me what to change.",
        )
    return TurnResult(updates={"confirmed": {"value": True}}, complete=True)


STAGES: dict[OnboardingStage, StageSpec] = {
    OnboardingStage.WELCOME: StageSpec(_question_welcome, _process_welcome),
    OnboardingStage.CATEGORY_SELECT: StageSpec(_question_category, _process_category),
    OnboardingStage.BUSINESS_INFO: StageSpec(_question_business_info, _process_business_info),
    OnboardingStage.BUSINESS_OVERVIEW: StageSpec(_question_overview, _process_overview_stage),
    OnboardingStage.TARGET_AUDIENCE: StageSpec(_question_audience, _process_audience),
    OnboardingStage.EXISTING_CUSTOMERS: StageSpec(_question_existing, _process_existing),
    OnboardingStage.COMPETITOR_ANALYSIS: StageSpec(_question_competitors, _process_competitors),
    OnboardingStage.BRAND_IDENTITY: StageSpec(_question_brand, _process_brand),
    OnboardingStage.CREATIVE_PREFERENCES: StageSpec(_question_creative, _process_creative),
    OnboardingStage.MARKETING_GOALS: StageSpec(_question_goals, _process_goals),
    OnboardingStage.LEAD_MANAGEMENT: StageSpec(_question_leads, _process_leads),
    OnboardingStage.CONFIRM_AND_CREATE: StageSpec(_question_confirm, _process_confirm),
}


async def process_turn(
    stage: OnboardingStage, message: str, data: dict[str, object]
) -> tuple[TurnResult, str]:
    """Run one turn; returns (result, next question or clarification text)."""
    spec = STAGES[stage]
    result: TurnResult = await spec.process(message, data)  # type: ignore[operator]
    if not result.complete:
        return result, result.clarification or "Could you tell me a bit more?"
    following = next_stage(stage)
    if following is None:
        return result, "All done — your profile is being created!"
    question: str = STAGES[following].question({**data, **result.updates})  # type: ignore[operator]
    return result, question

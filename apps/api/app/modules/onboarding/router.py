"""Onboarding chat endpoint.

POST /onboarding/message is UNAUTHENTICATED through the eleven collection
stages — the prospect has no account yet; identity is the session-token
cookie. The final CONFIRM_AND_CREATE turn requires authentication (the
account exists by then) and materialises all six profile tables in one
transaction.
"""

import logging

from fastapi import APIRouter, Request, Response
from pydantic import Field
from sqlalchemy import select

from app.core.config import settings
from app.core.schemas import MESSAGE_MAX, SanitizedModel, clean_display_text
from app.db.models import (
    AuditAction,
    BrandKit,
    BusinessProfile,
    CompetitorAnalysis,
    CustomerPersona,
    MarketingConfig,
)
from app.gateway.dependencies import AuthenticatedUser, get_current_user
from app.modules.audit.service import log_event
from app.modules.onboarding import session_service
from app.modules.onboarding.state_machine import (
    STAGES,
    OnboardingStage,
    OnboardingTurnResponse,
    next_stage,
    process_turn,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

SESSION_COOKIE = "onboarding_session"


class OnboardingMessage(SanitizedModel):
    message: str = Field(min_length=1, max_length=MESSAGE_MAX)


@router.post("/message", summary="Advance the onboarding conversation by one turn")
async def onboarding_message(
    body: OnboardingMessage, request: Request, response: Response
) -> OnboardingTurnResponse:
    token = request.cookies.get(SESSION_COOKIE, "")
    session_data = await session_service.load_session(token) if token else None

    if session_data is None:
        token = session_service.new_session_token()
        session_data = session_service.OnboardingSessionData(token=token)
        response.set_cookie(
            SESSION_COOKIE,
            token,
            max_age=session_service.SESSION_TTL_S,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",  # onboarding may be entered from marketing links
            path="/api/v1/onboarding",
        )
        first_question = STAGES[OnboardingStage.WELCOME].question({})  # type: ignore[operator]
        await session_service.save_session(session_data)
        return OnboardingTurnResponse(
            stage=session_data.stage.value, reply=str(first_question), advanced=False
        )

    stage = session_data.stage

    # The final stage needs a logged-in user (account exists by now)
    if stage is OnboardingStage.CONFIRM_AND_CREATE:
        try:
            user = await get_current_user(request)
        except Exception:  # noqa: BLE001 — surfaced as a friendly chat reply
            return OnboardingTurnResponse(
                stage=stage.value,
                reply="Almost there — please register or log in, then say 'confirm'.",
                advanced=False,
                requires_auth=True,
            )
        result, reply = await process_turn(
            stage, body.message, {**session_data.answers, "__token": token}
        )
        if not result.complete:
            return OnboardingTurnResponse(stage=stage.value, reply=reply, advanced=False)
        await _materialise_profile(user, session_data)
        return OnboardingTurnResponse(
            stage=stage.value,
            reply="Your profile is live! Head to your dashboard — your AI is ready.",
            advanced=True,
            completed=True,
        )

    result, reply = await process_turn(
        stage, body.message, {**session_data.answers, "__token": token}
    )
    if result.complete:
        session_data.answers.update(
            {k: v for k, v in result.updates.items() if isinstance(v, dict)}
        )
        following = next_stage(stage)
        if following is not None:
            session_data.stage = following
    await session_service.save_session(session_data)
    return OnboardingTurnResponse(
        stage=session_data.stage.value, reply=reply, advanced=result.complete
    )


async def _materialise_profile(
    user: AuthenticatedUser, data: session_service.OnboardingSessionData
) -> None:
    """Write all six profile tables from the collected answers, atomically."""
    from app.db.base import get_session_factory, with_tenant_scope

    answers = data.answers
    category = str(answers.get("category", {}).get("key", "home_cleaning"))
    business_raw = clean_display_text(str(answers.get("business_info", {}).get("raw", "")))
    services = answers.get("services", {})
    audience = answers.get("target_audience", {})
    competitors = answers.get("competitors", {})
    brand = answers.get("brand_identity", {})
    creative = answers.get("creative_preferences", {})
    goals = answers.get("marketing_goals", {})
    leads = answers.get("lead_management", {})
    existing = answers.get("existing_customers", {})

    factory = get_session_factory()
    async with factory() as session:
        async with with_tenant_scope(session, user.tenant_id):
            session.add(
                BusinessProfile(
                    tenant_id=user.tenant_id,
                    category=category,
                    business_name=business_raw[:255] or "My Business",
                    description=str(existing.get("raw", "")) or None,
                    services={"items": services.get("services", [])},
                    faqs={"target_audience": audience},
                )
            )
            session.add(
                CustomerPersona(
                    tenant_id=user.tenant_id,
                    name="Primary persona",
                    description=str(audience.get("description", "")) or None,
                    attributes=dict(audience),
                )
            )
            raw_names = competitors.get("competitors", [])
            names = list(raw_names) if isinstance(raw_names, list) else []
            for name in names[:10]:
                session.add(
                    CompetitorAnalysis(
                        tenant_id=user.tenant_id,
                        competitor_name=clean_display_text(str(name))[:255],
                        data={"differentiators": competitors.get("differentiators", [])},
                    )
                )
            session.add(
                MarketingConfig(
                    tenant_id=user.tenant_id,
                    goals={"raw": goals.get("raw", "")},
                    target_audience=dict(audience),
                    posting_schedule={"creative_preferences": creative.get("raw", "")},
                )
            )
            session.add(
                BrandKit(
                    tenant_id=user.tenant_id,
                    colors={"raw": brand.get("raw", "")},
                    fonts={"lead_management": leads.get("raw", "")},
                )
            )
            await session.flush()
            profile_id = await session.scalar(select(BusinessProfile.id))
            await log_event(
                session,
                action=AuditAction.CREATE,
                resource_type="BusinessProfile",
                resource_id=profile_id,
                tenant_id=user.tenant_id,
                actor_user_id=user.user_id,
                new_values={"category": category, "via": "onboarding"},
            )
        await session.commit()

    # Pre-compute the image style prompt now that the brand kit exists
    # [CANVA_NEXT_UPDATE] this trigger will call Canva brand kit creation instead
    try:
        from app.worker.tasks import compute_nanobanana_style_prompt

        compute_nanobanana_style_prompt.delay(str(user.tenant_id))
    except Exception:  # noqa: BLE001
        logger.warning("style prompt task enqueue failed")

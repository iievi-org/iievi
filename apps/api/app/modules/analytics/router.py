"""Onboarding analytics events — stage completions, time-per-stage, drop-offs.

Unauthenticated (onboarding happens pre-account); addressed by session token.
The first analytics signal showing where the onboarding flow loses people.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schemas import SanitizedModel
from app.db.base import get_session
from app.db.models import OnboardingEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


class OnboardingEventIn(SanitizedModel):
    session_token: str = Field(min_length=16, max_length=64)
    stage: str = Field(min_length=2, max_length=32)
    event_type: str = Field(min_length=2, max_length=48)
    metadata: dict[str, object] = Field(default_factory=dict)


@router.post(
    "/onboarding-event",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Record one onboarding funnel event",
)
async def record_onboarding_event(
    body: OnboardingEventIn,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, str]:
    session.add(
        OnboardingEvent(
            session_token=body.session_token,
            stage=body.stage,
            event_type=body.event_type,
            meta=body.metadata,
        )
    )
    return {"status": "recorded"}

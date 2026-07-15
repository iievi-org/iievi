"""Onboarding session storage: Redis-first with async DB fallback.

Key: onboarding:{session_token}, TTL 24h refreshed on every message. Every
Redis write also fire-and-forgets a Celery task that upserts the
onboarding_sessions row, so an abandoned session survives Redis eviction
and can be resumed days later.
"""

import json
import logging
import secrets

from pydantic import BaseModel, Field

from app.core.redis import get_redis
from app.modules.onboarding.state_machine import OnboardingStage

logger = logging.getLogger(__name__)

SESSION_TTL_S = 24 * 3600
_KEY_PREFIX = "onboarding:"


class OnboardingSessionData(BaseModel):
    """Everything collected so far, organised by stage."""

    token: str
    stage: OnboardingStage = OnboardingStage.WELCOME
    answers: dict[str, dict[str, object]] = Field(default_factory=dict)


def _as_answer_dict(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict):
        return {}
    return {str(k): dict(v) for k, v in value.items() if isinstance(v, dict)}


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


async def load_session(token: str) -> OnboardingSessionData | None:
    raw = await get_redis().get(f"{_KEY_PREFIX}{token}")
    if raw is not None:
        return OnboardingSessionData.model_validate_json(raw)
    # Redis miss → DB fallback (session may have outlived the 24h TTL)
    from sqlalchemy import select

    from app.db.base import get_session_factory
    from app.db.models import OnboardingSession

    factory = get_session_factory()
    async with factory() as session:
        row = await session.scalar(
            select(OnboardingSession).where(OnboardingSession.session_token == token)
        )
    if row is None:
        return None
    data = OnboardingSessionData(
        token=token,
        stage=OnboardingStage(row.current_stage),
        answers=_as_answer_dict(row.data.get("answers", {})),
    )
    await save_session(data)  # re-warm Redis
    return data


async def save_session(data: OnboardingSessionData) -> None:
    await get_redis().set(f"{_KEY_PREFIX}{data.token}", data.model_dump_json(), ex=SESSION_TTL_S)
    # Fire-and-forget durability; onboarding must not block on the DB write.
    try:
        from app.worker.tasks import persist_onboarding_session

        persist_onboarding_session.delay(
            token=data.token,
            stage=data.stage.value,
            answers=json.loads(json.dumps(data.answers, default=str)),
        )
    except Exception:  # noqa: BLE001 — broker down must not break onboarding
        logger.warning("could not enqueue onboarding persistence task")

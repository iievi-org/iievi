"""Feature flag administration — platform-admin only.

Every mutation invalidates the Redis cache (the service's 60s TTL would
otherwise serve stale flags) and writes an audit record.
"""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ResourceNotFoundError
from app.core.redis import get_redis
from app.core.schemas import DESCRIPTION_MAX, SanitizedModel
from app.db.base import get_session
from app.db.models import AuditAction, FeatureFlag, Plan
from app.gateway.dependencies import AdminUser, require_admin
from app.modules.audit.service import log_event
from app.services.feature_flags import FeatureFlagService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/feature-flags",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


class FlagCreate(SanitizedModel):
    flag_key: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9_.-]+$")
    description: str = Field(default="", max_length=DESCRIPTION_MAX)
    enabled_globally: bool = False
    minimum_plan: Plan | None = None


class FlagPatch(SanitizedModel):
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX)
    enabled_globally: bool | None = None
    minimum_plan: Plan | None = None
    add_enabled_tenants: list[uuid.UUID] = Field(default_factory=list)
    remove_enabled_tenants: list[uuid.UUID] = Field(default_factory=list)
    add_disabled_tenants: list[uuid.UUID] = Field(default_factory=list)
    remove_disabled_tenants: list[uuid.UUID] = Field(default_factory=list)


class FlagOut(SanitizedModel):
    flag_key: str
    description: str | None
    enabled_globally: bool
    enabled_for_tenants: list[uuid.UUID]
    disabled_for_tenants: list[uuid.UUID]
    minimum_plan: Plan | None


def _to_out(flag: FeatureFlag) -> FlagOut:
    return FlagOut(
        flag_key=flag.flag_key,
        description=flag.description,
        enabled_globally=flag.enabled_globally,
        enabled_for_tenants=list(flag.enabled_for_tenants),
        disabled_for_tenants=list(flag.disabled_for_tenants),
        minimum_plan=flag.minimum_plan,
    )


async def _get_or_404(session: AsyncSession, key: str) -> FeatureFlag:
    flag = await session.scalar(select(FeatureFlag).where(FeatureFlag.flag_key == key))
    if flag is None:
        raise ResourceNotFoundError(f"feature flag {key!r} does not exist")
    return flag


@router.get("", summary="List all feature flags", response_model=list[FlagOut])
async def list_flags(session: Annotated[AsyncSession, Depends(get_session)]) -> list[FlagOut]:
    flags = (await session.scalars(select(FeatureFlag).order_by(FeatureFlag.flag_key))).all()
    return [_to_out(f) for f in flags]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a feature flag",
    response_model=FlagOut,
)
async def create_flag(
    body: FlagCreate, user: AdminUser, session: Annotated[AsyncSession, Depends(get_session)]
) -> FlagOut:
    flag = FeatureFlag(
        flag_key=body.flag_key,
        description=body.description,
        enabled_globally=body.enabled_globally,
        minimum_plan=body.minimum_plan,
    )
    session.add(flag)
    await session.flush()
    await log_event(
        session,
        action=AuditAction.CREATE,
        resource_type="FeatureFlag",
        resource_id=flag.id,
        actor_user_id=user.user_id,
        new_values={"flag_key": body.flag_key, "enabled_globally": body.enabled_globally},
    )
    return _to_out(flag)


@router.patch("/{key}", summary="Toggle a flag or adjust tenant lists", response_model=FlagOut)
async def patch_flag(
    key: str,
    body: FlagPatch,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FlagOut:
    flag = await _get_or_404(session, key)
    old = {"enabled_globally": flag.enabled_globally, "minimum_plan": flag.minimum_plan}

    if body.description is not None:
        flag.description = body.description
    if body.enabled_globally is not None:
        flag.enabled_globally = body.enabled_globally
    if body.minimum_plan is not None:
        flag.minimum_plan = body.minimum_plan

    enabled = set(flag.enabled_for_tenants) | set(body.add_enabled_tenants)
    enabled -= set(body.remove_enabled_tenants)
    flag.enabled_for_tenants = sorted(enabled, key=str)

    disabled = set(flag.disabled_for_tenants) | set(body.add_disabled_tenants)
    disabled -= set(body.remove_disabled_tenants)
    flag.disabled_for_tenants = sorted(disabled, key=str)

    await session.flush()
    await FeatureFlagService(session, get_redis()).invalidate(key)
    await log_event(
        session,
        action=AuditAction.UPDATE,
        resource_type="FeatureFlag",
        resource_id=flag.id,
        actor_user_id=user.user_id,
        old_values=dict(old),
        new_values={
            "enabled_globally": flag.enabled_globally,
            "minimum_plan": flag.minimum_plan,
        },
    )
    return _to_out(flag)


@router.delete(
    "/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a feature flag (requires ?confirm=true)",
)
async def delete_flag(
    key: str,
    user: AdminUser,
    session: Annotated[AsyncSession, Depends(get_session)],
    confirm: bool = Query(default=False, description="Must be true — deletion is permanent"),
) -> None:
    if not confirm:
        raise BadRequestError("pass ?confirm=true to delete a feature flag")
    flag = await _get_or_404(session, key)
    await session.delete(flag)
    await session.flush()
    await FeatureFlagService(session, get_redis()).invalidate(key)
    await log_event(
        session,
        action=AuditAction.DELETE,
        resource_type="FeatureFlag",
        resource_id=flag.id,
        actor_user_id=user.user_id,
        old_values={"flag_key": key},
    )

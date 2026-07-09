"""Central dependency-injection chain for every protected endpoint.

Three independent layers make cross-tenant access architecturally impossible:
1. get_current_user — JWT signature/expiry/blacklist (transport layer)
2. get_scoped_session — sets app.current_tenant_id for RLS (database layer)
3. require_plan / check_permission / require_admin — feature gating

Route handlers NEVER take tenant_id from the request body or query string;
the only tenant identity in the system is the JWT tid claim.
"""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.permissions import Permission, role_has_permission
from app.core.security import TokenError, decode_access_token
from app.db.base import get_session, with_tenant_scope
from app.db.models import Plan, UserRole

PLAN_HIERARCHY: dict[str, int] = {
    Plan.TRIAL.value: 0,
    Plan.STARTER.value: 1,
    Plan.GROWTH.value: 2,
    Plan.AGENCY.value: 3,
}


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity extracted from a verified access token."""

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    plan: str
    role: UserRole
    is_admin: bool


async def get_current_user(request: Request) -> AuthenticatedUser:
    """Verify the Bearer token (signature, expiry, blacklist) or 401."""
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Missing or malformed Authorization header")
    try:
        payload = await decode_access_token(token)
    except TokenError as exc:
        raise AuthenticationError(str(exc)) from exc
    try:
        role = UserRole(payload.role)
    except ValueError as exc:
        raise AuthenticationError("Unknown role claim") from exc
    user = AuthenticatedUser(
        user_id=uuid.UUID(payload.sub),
        tenant_id=uuid.UUID(payload.tid),
        plan=payload.plan,
        role=role,
        is_admin=payload.admin,
    )
    # Expose identity to middleware (access logging, rate limiting tier 2)
    request.state.user = user
    from app.core.context import tenant_id_var

    tenant_id_var.set(str(user.tenant_id))
    return user


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


async def get_scoped_session(
    user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncIterator[AsyncSession]:
    """Yield a session with the RLS tenant context set for this user's tenant."""
    async with with_tenant_scope(session, user.tenant_id) as scoped:
        yield scoped


ScopedSession = Annotated[AsyncSession, Depends(get_scoped_session)]


def require_plan(minimum_plan: str) -> Callable[[AuthenticatedUser], Awaitable[AuthenticatedUser]]:
    """Dependency factory: 403 plan_upgrade_required below `minimum_plan`."""
    if minimum_plan not in PLAN_HIERARCHY:  # fail at import, not at request time
        msg = f"unknown plan: {minimum_plan}"
        raise ValueError(msg)

    async def _check(user: CurrentUser) -> AuthenticatedUser:
        if PLAN_HIERARCHY[user.plan] < PLAN_HIERARCHY[minimum_plan]:
            raise AuthorizationError(
                f"This feature requires the {minimum_plan} plan",
                details={
                    "code": "plan_upgrade_required",
                    "current_plan": user.plan,
                    "required_plan": minimum_plan,
                },
            )
        return user

    return _check


def check_permission(
    permission: Permission,
) -> Callable[[AuthenticatedUser], Awaitable[AuthenticatedUser]]:
    """Dependency factory: 403 unless the user's role grants `permission`."""

    async def _check(user: CurrentUser) -> AuthenticatedUser:
        if not role_has_permission(user.role, permission):
            raise AuthorizationError(
                f"Your role ({user.role.value}) does not allow {permission.value}",
                details={"required_permission": permission.value, "role": user.role.value},
            )
        return user

    return _check


async def require_admin(user: CurrentUser) -> AuthenticatedUser:
    """403 unless the token carries the platform-admin flag."""
    if not user.is_admin:
        raise AuthorizationError("Platform administrator access required")
    return user


AdminUser = Annotated[AuthenticatedUser, Depends(require_admin)]

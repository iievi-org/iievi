"""Authentication service: registration, login, token issuance.

Login-by-email must work BEFORE any tenant context exists, but the users
table is RLS-protected. The auth_lookup_user() SECURITY DEFINER function
(created in the gateway migration, owned by the table owner) is the single
sanctioned hole: it returns exactly the fields needed to verify a login and
nothing else. Email is globally unique (enforced by index) so the lookup is
unambiguous.

Login is constant-time with respect to account existence: when the email is
unknown we still verify the password against a static dummy bcrypt hash, so
the response time never reveals whether an email is registered.
"""

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import text

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.db.base import get_session_factory, with_tenant_scope
from app.db.models import AuditAction, Plan, Tenant, TenantStatus, User, UserRole
from app.modules.audit.service import log_event

logger = logging.getLogger(__name__)

# bcrypt cost-12 hash of a random UUID burned at module load — used to keep
# login timing constant for unknown emails. Never matches any real password.
_DUMMY_HASH = hash_password(str(uuid.uuid4()))


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    user_id: uuid.UUID
    tenant_id: uuid.UUID


def _issue(user_id: uuid.UUID, tenant_id: uuid.UUID, plan: str, role: str) -> IssuedTokens:
    access = create_access_token(
        {"sub": str(user_id), "tid": str(tenant_id), "plan": plan, "role": role, "admin": False}
    )
    refresh = create_refresh_token(str(user_id))
    return IssuedTokens(
        access_token=access, refresh_token=refresh, user_id=user_id, tenant_id=tenant_id
    )


async def register(
    *, business_name: str, full_name: str, email: str, password: str, actor_ip: str | None
) -> IssuedTokens:
    """Create tenant + owner user atomically (both or neither)."""
    factory = get_session_factory()
    async with factory() as session:
        # Global email uniqueness pre-check via the definer function (the
        # unique index is the real guarantee; this gives a clean error).
        existing = await session.execute(
            text("SELECT user_id FROM auth_lookup_user(:email)"), {"email": email}
        )
        if existing.first() is not None:
            raise AuthenticationError("An account with this email already exists")

        tenant = Tenant(name=business_name, status=TenantStatus.ACTIVE, plan=Plan.TRIAL)
        session.add(tenant)
        await session.flush()  # materialise tenant.id for the RLS context

        async with with_tenant_scope(session, tenant.id):
            user = User(
                tenant_id=tenant.id,
                email=email.lower(),
                password_hash=hash_password(password),
                full_name=full_name,
                role=UserRole.OWNER,
            )
            session.add(user)
            await session.flush()
            await log_event(
                session,
                action=AuditAction.CREATE,
                resource_type="Tenant",
                resource_id=tenant.id,
                tenant_id=tenant.id,
                actor_user_id=user.id,
                actor_ip=actor_ip,
                new_values={"business_name": business_name, "email": email.lower()},
            )
            tokens = _issue(user.id, tenant.id, Plan.TRIAL.value, UserRole.OWNER.value)
        await session.commit()
        return tokens


@dataclass(frozen=True)
class RefreshClaims:
    tenant_id: uuid.UUID
    plan: str
    role: str


async def lookup_claims(user_id: str) -> RefreshClaims:
    """Current plan/role/status for token refresh (SECURITY DEFINER lookup)."""
    factory = get_session_factory()
    async with factory() as session:
        row = (
            await session.execute(
                text(
                    "SELECT tenant_id, plan, role, is_active, tenant_status "
                    "FROM auth_lookup_claims(:uid)"
                ),
                {"uid": user_id},
            )
        ).first()
    if row is None or not row.is_active:
        raise AuthenticationError("Account no longer active")
    if row.tenant_status == TenantStatus.SUSPENDED.value:
        raise AuthenticationError("This workspace is suspended — contact support")
    return RefreshClaims(tenant_id=row.tenant_id, plan=str(row.plan), role=str(row.role))


async def login(*, email: str, password: str, actor_ip: str | None) -> IssuedTokens:
    """Verify credentials in constant time; 401 on any failure."""
    factory = get_session_factory()
    async with factory() as session:
        row = (
            await session.execute(
                text(
                    "SELECT user_id, tenant_id, password_hash, role, is_active, "
                    "tenant_status, plan FROM auth_lookup_user(:email)"
                ),
                {"email": email},
            )
        ).first()

        if row is None:
            verify_password(password, _DUMMY_HASH)  # constant-time decoy
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, row.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not row.is_active:
            raise AuthenticationError("This account has been deactivated")
        if row.tenant_status == TenantStatus.SUSPENDED.value:
            raise AuthenticationError("This workspace is suspended — contact support")

        tokens = _issue(row.user_id, row.tenant_id, str(row.plan), str(row.role))
        async with with_tenant_scope(session, row.tenant_id):
            await session.execute(
                text("UPDATE users SET last_login_at = now() WHERE id = :uid"),
                {"uid": row.user_id},
            )
            await log_event(
                session,
                action=AuditAction.LOGIN,
                resource_type="User",
                resource_id=row.user_id,
                tenant_id=row.tenant_id,
                actor_user_id=row.user_id,
                actor_ip=actor_ip,
            )
        await session.commit()
        return tokens

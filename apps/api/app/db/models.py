"""Complete IIEVI database schema — SQLAlchemy 2.0 typed declarative models.

Conventions (enforced, see .claude/memory/quality-checks.md):
- Every tenant-scoped model carries `tenant_id` FK → tenants.id ON DELETE
  CASCADE and gets an RLS policy in the `apply_rls` migration.
- Tables WITHOUT RLS, deliberately: platform_identifiers (webhook routing
  happens before tenant context exists), webhook_events (same reason),
  audit_logs (platform-level compliance record), feature_flags (global).
- Money is Integer paise. Timestamps are TIMESTAMPTZ. PKs are UUIDs
  generated server-side by gen_random_uuid(). Enums are native PG enums.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class Plan(enum.StrEnum):
    TRIAL = "trial"
    STARTER = "starter"
    GROWTH = "growth"
    AGENCY = "agency"


class TenantStatus(enum.StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class UserRole(enum.StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class LeadSource(enum.StrEnum):
    COMMENT = "comment"
    DIRECT_MESSAGE = "direct_message"
    WHATSAPP = "whatsapp"
    STORY_REPLY = "story_reply"
    AD_CLICK = "ad_click"
    MANUAL = "manual"


class LeadStatus(enum.StrEnum):
    NEW = "new"
    ENGAGED = "engaged"
    QUALIFIED = "qualified"
    BOOKED = "booked"
    WON = "won"
    LOST = "lost"


class ConversationRole(enum.StrEnum):
    LEAD = "lead"
    ASSISTANT = "assistant"
    HUMAN_AGENT = "human_agent"
    SYSTEM = "system"


class Platform(enum.StrEnum):
    META = "meta"
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class PostStatus(enum.StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"


class AdObjective(enum.StrEnum):
    REACH = "reach"
    ENGAGEMENT = "engagement"
    LEADS = "leads"
    MESSAGES = "messages"
    CONVERSIONS = "conversions"


class AdStatus(enum.StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    REJECTED = "rejected"


class SubscriptionStatus(enum.StrEnum):
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class AuditAction(enum.StrEnum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    CREDENTIAL_ACCESS = "credential_access"
    PLAN_CHANGE = "plan_change"
    SUSPENSION = "suspension"


class IdempotencyStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Base + mixins
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Declarative base with project-wide type defaults."""

    type_annotation_map = {
        datetime: TIMESTAMP(timezone=True),
        dict[str, object]: JSONB,
    }


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )


def _created_at() -> Mapped[datetime]:
    return mapped_column(server_default=text("now()"), nullable=False)


def _updated_at() -> Mapped[datetime]:
    return mapped_column(server_default=text("now()"), onupdate=text("now()"), nullable=False)


def _tenant_fk() -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)


# ---------------------------------------------------------------------------
# Core tables
# ---------------------------------------------------------------------------


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenant_status", values_callable=lambda e: [m.value for m in e]),
        default=TenantStatus.ACTIVE,
        server_default=TenantStatus.ACTIVE.value,
    )
    plan: Mapped[Plan] = mapped_column(
        Enum(Plan, name="plan", values_callable=lambda e: [m.value for m in e]),
        default=Plan.TRIAL,
        server_default=Plan.TRIAL.value,
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    users: Mapped[list["User"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    email: Mapped[str] = mapped_column(String(320))
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]),
        default=UserRole.OWNER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    tenant: Mapped[Tenant] = relationship(back_populates="users")


class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    category: Mapped[str] = mapped_column(String(64))
    business_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Services the AI is allowed to talk about — the grounding source of truth
    services: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    pricing: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    hours: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    locations: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    faqs: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    policies: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class CustomerPersona(Base):
    __tablename__ = "customer_personas"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class CompetitorAnalysis(Base):
    __tablename__ = "competitor_analysis"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    competitor_name: Mapped[str] = mapped_column(String(255))
    data: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class MarketingConfig(Base):
    __tablename__ = "marketing_configs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    tone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    goals: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    posting_schedule: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    target_audience: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class BrandKit(Base):
    __tablename__ = "brand_kits"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # R2 object key — signed URLs are generated on demand, never stored
    logo_r2_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Pre-computed by the compute_nanobanana_style_prompt Celery task
    # [CANVA_NEXT_UPDATE] replaced by a Canva brand-kit reference when Canva lands
    nanobanana_style_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    colors: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    fonts: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    # [CANVA_NEXT_UPDATE] Canva brand template references will be stored here
    templates: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class ApiCredential(Base):
    __tablename__ = "api_credentials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "service", name="uq_api_credentials_tenant_service"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    service: Mapped[str] = mapped_column(String(64))  # anthropic | nanobanana | meta | ...
    # AES-256-GCM, format base64(iv):base64(ciphertext+tag) — see core/security.py
    encrypted_key: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'")
    )
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class PlatformIdentifier(Base):
    """Webhook routing: external page/account id → tenant. Deliberately NO RLS."""

    __tablename__ = "platform_identifiers"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_platform_identifiers_ext"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform, name="platform", values_callable=lambda e: [m.value for m in e])
    )
    external_id: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = _created_at()


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        UniqueConstraint("tenant_id", "platform_id", name="uq_leads_tenant_platform_id"),
        Index("ix_leads_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    source: Mapped[LeadSource] = mapped_column(
        Enum(LeadSource, name="lead_source", values_callable=lambda e: [m.value for m in e])
    )
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status", values_callable=lambda e: [m.value for m in e]),
        default=LeadStatus.NEW,
        server_default=LeadStatus.NEW.value,
    )
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform, name="platform", values_callable=lambda e: [m.value for m in e])
    )
    # The lead's id on the source platform (IG user id, WhatsApp number, ...)
    platform_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    # Drives the WhatsApp 24-hour messaging window check
    last_inbound_at: Mapped[datetime | None] = mapped_column(nullable=True)
    meta: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="lead")


class Conversation(Base):
    """One message in a lead conversation (event-log style, append-mostly)."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[ConversationRole] = mapped_column(
        Enum(
            ConversationRole,
            name="conversation_role",
            values_callable=lambda e: [m.value for m in e],
        )
    )
    content: Mapped[str] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = _created_at()

    lead: Mapped[Lead] = relationship(back_populates="conversations")


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_tenant_status", "tenant_id", "status"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus, name="post_status", values_callable=lambda e: [m.value for m in e]),
        default=PostStatus.DRAFT,
        server_default=PostStatus.DRAFT.value,
    )
    platforms: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_urls: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    # Per-platform post ids after publishing, keyed by platform name
    platform_post_ids: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    plan: Mapped[Plan] = mapped_column(
        Enum(Plan, name="plan", values_callable=lambda e: [m.value for m in e])
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(
            SubscriptionStatus,
            name="subscription_status",
            values_callable=lambda e: [m.value for m in e],
        )
    )
    provider: Mapped[str] = mapped_column(String(32))  # razorpay | stripe
    provider_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
    )
    amount_paise: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="INR", server_default="INR")
    current_period_start: Mapped[datetime | None] = mapped_column(nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class MonthlyUsage(Base):
    __tablename__ = "monthly_usage"
    __table_args__ = (UniqueConstraint("tenant_id", "month", name="uq_monthly_usage_tenant_month"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    month: Mapped[date] = mapped_column(Date)  # first day of the month
    posts_generated: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    images_generated: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    ai_messages: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    leads_captured: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    tokens_used: Mapped[int] = mapped_column(BigInteger, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class AuditLog(Base):
    """Append-only compliance record. NO RLS (platform-level), no UPDATE/DELETE ever."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_tenant_created", "tenant_id", "created_at"),
        Index(
            "ix_audit_logs_metadata_gin",
            "metadata",
            postgresql_using="gin",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    # Bare UUID, deliberately NO foreign key: audit rows are immutable history
    # (append-only trigger) — an FK ON DELETE action would need to UPDATE them.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    # Nullable: system actions (Celery tasks, webhooks) have no acting user
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action", values_callable=lambda e: [m.value for m in e])
    )
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    old_values: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    meta: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()


class FeatureFlag(Base):
    """Global flag definitions. NO RLS — evaluated per-tenant in FeatureFlagService."""

    __tablename__ = "feature_flags"

    id: Mapped[uuid.UUID] = _uuid_pk()
    flag_key: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled_globally: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    enabled_for_tenants: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, server_default=text("'{}'")
    )
    disabled_for_tenants: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, server_default=text("'{}'")
    )
    minimum_plan: Mapped[Plan | None] = mapped_column(
        Enum(Plan, name="plan", values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    meta: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class WebhookEvent(Base):
    """Idempotency log for ALL incoming webhooks. NO RLS (pre-tenant-context)."""

    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    platform_event_id: Mapped[str] = mapped_column(String(255), unique=True)
    platform: Mapped[str] = mapped_column(String(32))  # meta | whatsapp | razorpay | stripe...
    event_type: Mapped[str] = mapped_column(String(128))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    idempotency_status: Mapped[IdempotencyStatus] = mapped_column(
        Enum(
            IdempotencyStatus,
            name="idempotency_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=IdempotencyStatus.PENDING,
        server_default=IdempotencyStatus.PENDING.value,
    )
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    received_at: Mapped[datetime] = _created_at()


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_notification_prefs_tenant_user"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    tenant_id: Mapped[uuid.UUID] = _tenant_fk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    whatsapp_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    # Per-event-type overrides, e.g. {"new_lead": {"email": false}}
    overrides: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class OnboardingSession(Base):
    """DB fallback for Redis-held onboarding sessions. NO RLS — onboarding
    happens BEFORE a tenant account exists (session-token addressed)."""

    __tablename__ = "onboarding_sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    session_token: Mapped[str] = mapped_column(String(64), unique=True)
    current_stage: Mapped[str] = mapped_column(String(32))
    data: Mapped[dict[str, object]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'")
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class OnboardingEvent(Base):
    """Lightweight onboarding analytics (stage completions, drop-offs).
    NO RLS — recorded before any tenant exists."""

    __tablename__ = "onboarding_events"
    __table_args__ = (Index("ix_onboarding_events_token", "session_token", "created_at"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    session_token: Mapped[str] = mapped_column(String(64))
    stage: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(48))
    meta: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, default=dict, server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = _created_at()


# Tables that get RLS policies in the apply_rls migration. Order matters for
# readability only. platform_identifiers / audit_logs / feature_flags /
# webhook_events are intentionally absent — see module docstring.
TENANT_SCOPED_TABLES: tuple[str, ...] = (
    "users",
    "business_profiles",
    "customer_personas",
    "competitor_analysis",
    "marketing_configs",
    "brand_kits",
    "api_credentials",
    "leads",
    "conversations",
    "posts",
    "subscriptions",
    "monthly_usage",
    "notification_preferences",
)

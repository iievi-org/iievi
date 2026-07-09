"""Profile endpoints: the complete profile in one request, partial updates,
service management, logo upload, completeness.

Every write audits via the audit service and fires the profile hooks.
"""

import io
import logging

from fastapi import APIRouter, UploadFile
from pydantic import Field
from sqlalchemy import select

from app.core.exceptions import BadRequestError, ResourceNotFoundError
from app.core.r2_service import DISPLAY_URL_TTL_S, build_object_key, r2_service
from app.core.schemas import DESCRIPTION_MAX, NAME_MAX, SanitizedModel, clean_display_text
from app.db.models import (
    AuditAction,
    BrandKit,
    BusinessProfile,
    CompetitorAnalysis,
    CustomerPersona,
    MarketingConfig,
)
from app.gateway.dependencies import CurrentUser, ScopedSession
from app.modules.audit.service import log_event
from app.modules.profiles.completeness import compute_completeness
from app.modules.profiles.hooks import after_profile_write

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profiles", tags=["profiles"])

LOGO_MAX_BYTES = 5 * 1024 * 1024
LOGO_MIN_DIM = 100
LOGO_MAX_DIM = 4000
LOGO_RESIZE_TO = 1000
_ALLOWED_LOGO_MIME = {"image/png": "png", "image/jpeg": "jpg", "image/svg+xml": "svg"}


class ServiceIn(SanitizedModel):
    name: str = Field(min_length=2, max_length=NAME_MAX)
    price_min_paise: int | None = Field(default=None, ge=0)
    price_max_paise: int | None = Field(default=None, ge=0)
    unit: str = Field(default="per job", max_length=64)


class ProfileUpdate(SanitizedModel):
    business_name: str | None = Field(default=None, min_length=2, max_length=NAME_MAX)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX)
    hours: dict[str, object] | None = None
    locations: dict[str, object] | None = None
    faqs: dict[str, object] | None = None
    policies: dict[str, object] | None = None
    colors: dict[str, object] | None = None  # brand kit
    fonts: dict[str, object] | None = None  # brand kit
    tone: str | None = Field(default=None, max_length=64)  # marketing config
    goals: dict[str, object] | None = None  # marketing config


@router.get("", summary="Complete profile in a single request")
async def get_profile(user: CurrentUser, session: ScopedSession) -> dict[str, object]:
    """Joins BusinessProfile, CustomerPersona, CompetitorAnalysis,
    MarketingConfig, and BrandKit — the frontend never assembles a profile
    from multiple calls."""
    profile = await session.scalar(select(BusinessProfile))
    personas = (await session.scalars(select(CustomerPersona))).all()
    competitors = (await session.scalars(select(CompetitorAnalysis))).all()
    marketing = await session.scalar(select(MarketingConfig))
    kit = await session.scalar(select(BrandKit))

    logo_url: str | None = None
    if kit is not None and kit.logo_r2_key:
        try:
            logo_url = await r2_service.generate_signed_url(kit.logo_r2_key)
        except Exception:  # noqa: BLE001 — profile read must survive R2 outage
            logger.warning("signed logo URL generation failed")

    return {
        "business_profile": None
        if profile is None
        else {
            "category": profile.category,
            "business_name": profile.business_name,
            "description": profile.description,
            "services": profile.services,
            "pricing": profile.pricing,
            "hours": profile.hours,
            "locations": profile.locations,
            "faqs": profile.faqs,
            "policies": profile.policies,
        },
        "customer_personas": [
            {"name": p.name, "description": p.description, "attributes": p.attributes}
            for p in personas
        ],
        "competitor_analysis": [
            {"competitor_name": c.competitor_name, "data": c.data} for c in competitors
        ],
        "marketing_config": None
        if marketing is None
        else {
            "tone": marketing.tone,
            "goals": marketing.goals,
            "posting_schedule": marketing.posting_schedule,
            "target_audience": marketing.target_audience,
        },
        "brand_kit": None
        if kit is None
        else {"colors": kit.colors, "fonts": kit.fonts, "logo_url": logo_url},
    }


@router.put("", summary="Partial profile update")
async def update_profile(
    body: ProfileUpdate, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    profile = await session.scalar(select(BusinessProfile))
    if profile is None:
        raise ResourceNotFoundError("Complete onboarding before editing the profile")

    changed: list[str] = []
    old_values: dict[str, object] = {}

    for field in ("business_name", "description", "hours", "locations", "faqs", "policies"):
        value = getattr(body, field)
        if value is not None:
            old_values[field] = getattr(profile, field)
            if field in ("business_name", "description") and isinstance(value, str):
                value = clean_display_text(value)
            setattr(profile, field, value)
            changed.append(field)

    if body.colors is not None or body.fonts is not None:
        kit = await session.scalar(select(BrandKit))
        if kit is None:
            kit = BrandKit(tenant_id=user.tenant_id)
            session.add(kit)
        if body.colors is not None:
            old_values["colors"] = kit.colors
            kit.colors = body.colors
            changed.append("colors")
        if body.fonts is not None:
            old_values["fonts"] = kit.fonts
            kit.fonts = body.fonts
            changed.append("fonts")

    if body.tone is not None or body.goals is not None:
        marketing = await session.scalar(select(MarketingConfig))
        if marketing is None:
            marketing = MarketingConfig(tenant_id=user.tenant_id)
            session.add(marketing)
        if body.tone is not None:
            marketing.tone = clean_display_text(body.tone)
            changed.append("tone")
        if body.goals is not None:
            old_values["goals"] = marketing.goals
            marketing.goals = body.goals
            changed.append("goals")

    if not changed:
        raise BadRequestError("No fields to update")

    await session.flush()
    await log_event(
        session,
        action=AuditAction.UPDATE,
        resource_type="BusinessProfile",
        resource_id=profile.id,
        tenant_id=user.tenant_id,
        actor_user_id=user.user_id,
        old_values=old_values,
        new_values={field: True for field in changed},
    )
    after_profile_write(changed, user.tenant_id)
    return {"updated": changed}


@router.post("/services", status_code=201, summary="Add one service")
async def add_service(
    body: ServiceIn, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    profile = await session.scalar(select(BusinessProfile))
    if profile is None:
        raise ResourceNotFoundError("Complete onboarding before adding services")
    raw_items = profile.services.get("items", [])
    items = list(raw_items) if isinstance(raw_items, list) else []
    items.append(
        {
            "name": clean_display_text(body.name),
            "price_min_paise": body.price_min_paise,
            "price_max_paise": body.price_max_paise,
            "unit": body.unit,
        }
    )
    profile.services = {**profile.services, "items": items}
    await session.flush()
    await log_event(
        session,
        action=AuditAction.UPDATE,
        resource_type="BusinessProfile",
        resource_id=profile.id,
        tenant_id=user.tenant_id,
        actor_user_id=user.user_id,
        new_values={"service_added": body.name},
    )
    after_profile_write(["services"], user.tenant_id)
    return {"services": items}


@router.delete("/services/{index}", summary="Remove a service by array index")
async def delete_service(
    index: int, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    profile = await session.scalar(select(BusinessProfile))
    if profile is None:
        raise ResourceNotFoundError("No profile exists")
    raw_items = profile.services.get("items", [])
    items = list(raw_items) if isinstance(raw_items, list) else []
    if not 0 <= index < len(items):
        raise ResourceNotFoundError(f"No service at index {index}")
    removed = items.pop(index)
    profile.services = {**profile.services, "items": items}
    await session.flush()
    await log_event(
        session,
        action=AuditAction.UPDATE,
        resource_type="BusinessProfile",
        resource_id=profile.id,
        tenant_id=user.tenant_id,
        actor_user_id=user.user_id,
        old_values={"service_removed": removed},
    )
    after_profile_write(["services"], user.tenant_id)
    return {"services": items}


@router.get("/completeness", summary="Profile completeness score")
async def get_completeness(user: CurrentUser, session: ScopedSession) -> dict[str, object]:
    report = await compute_completeness(session)
    return {
        "percentage": report.percentage,
        "incomplete_sections": report.incomplete_sections,
    }


@router.post("/logo", summary="Upload the business logo")
async def upload_logo(
    file: UploadFile, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    """Validates MIME via magic bytes (not extension), size, and dimensions;
    resizes to ≤1000px (Lanczos); stores in R2; returns a signed URL."""
    import magic
    from PIL import Image

    raw = await file.read()
    if len(raw) > LOGO_MAX_BYTES:
        raise BadRequestError("Logo exceeds the 5MB limit")

    detected = magic.from_buffer(raw, mime=True)
    extension = _ALLOWED_LOGO_MIME.get(detected)
    if extension is None:
        raise BadRequestError(
            f"Unsupported file type {detected!r} — use PNG, JPEG, or SVG",
            details={"detected_mime": detected},
        )

    if detected != "image/svg+xml":
        try:
            image = Image.open(io.BytesIO(raw))
            image.load()
        except Exception as exc:  # noqa: BLE001
            raise BadRequestError("File is not a decodable image") from exc
        width, height = image.size
        if width < LOGO_MIN_DIM or height < LOGO_MIN_DIM:
            raise BadRequestError(f"Logo must be at least {LOGO_MIN_DIM}×{LOGO_MIN_DIM}px")
        if width > LOGO_MAX_DIM or height > LOGO_MAX_DIM:
            raise BadRequestError(f"Logo must be at most {LOGO_MAX_DIM}×{LOGO_MAX_DIM}px")
        if max(width, height) > LOGO_RESIZE_TO:
            image.thumbnail((LOGO_RESIZE_TO, LOGO_RESIZE_TO), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="PNG" if detected == "image/png" else "JPEG")
            raw = buffer.getvalue()

    key = build_object_key("logos", user.tenant_id, extension)
    await r2_service.upload(key, raw, detected)

    kit = await session.scalar(select(BrandKit))
    if kit is None:
        kit = BrandKit(tenant_id=user.tenant_id)
        session.add(kit)
    old_key = kit.logo_r2_key
    kit.logo_r2_key = key
    await session.flush()
    await log_event(
        session,
        action=AuditAction.UPDATE,
        resource_type="BrandKit",
        resource_id=kit.id,
        tenant_id=user.tenant_id,
        actor_user_id=user.user_id,
        old_values={"logo_r2_key": old_key},
        new_values={"logo_r2_key": key, "mime": detected, "bytes": len(raw)},
    )
    signed_url = await r2_service.generate_signed_url(key, DISPLAY_URL_TTL_S)
    return {"logo_key": key, "logo_url": signed_url}

"""Profile completeness scoring.

Weights (spec): business_info 10%, services 20%, target_audience 15%,
brand_identity 15%, marketing_goals 15%, credentials_connected 15%,
nanobanana_key 10%. Returns the percentage plus the incomplete sections so
the frontend can point the user at exactly what's missing.
"""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ApiCredential, BrandKit, BusinessProfile, MarketingConfig

WEIGHTS: dict[str, int] = {
    "business_info": 10,
    "services": 20,
    "target_audience": 15,
    "brand_identity": 15,
    "marketing_goals": 15,
    "credentials_connected": 15,
    "nanobanana_key": 10,
}


@dataclass(frozen=True)
class CompletenessReport:
    percentage: int
    incomplete_sections: list[str]


async def compute_completeness(session: AsyncSession) -> CompletenessReport:
    """Score the CURRENT tenant's profile (session must be tenant-scoped)."""
    profile = await session.scalar(select(BusinessProfile))
    kit = await session.scalar(select(BrandKit))
    marketing = await session.scalar(select(MarketingConfig))
    credentials = (await session.scalars(select(ApiCredential.service))).all()

    done: dict[str, bool] = {
        "business_info": profile is not None and bool(profile.business_name),
        "services": profile is not None and bool(profile.services),
        "target_audience": profile is not None
        and bool((profile.faqs or {}).get("target_audience") or profile.description),
        "brand_identity": kit is not None and bool(kit.colors),
        "marketing_goals": marketing is not None and bool(marketing.goals),
        "credentials_connected": any(s != "nanobanana" for s in credentials),
        "nanobanana_key": "nanobanana" in credentials,
    }

    score = sum(WEIGHTS[section] for section, complete in done.items() if complete)
    incomplete = [section for section, complete in done.items() if not complete]
    return CompletenessReport(percentage=score, incomplete_sections=incomplete)

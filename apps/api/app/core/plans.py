"""Plan limits — Python mirror of packages/constants PLAN_LIMITS.

Monthly quotas per plan. `None` means unlimited (Agency bypasses usage
checks entirely in usage_service). Keep in sync with the TS constants —
the frontend renders these numbers, the backend enforces them.
"""

from app.db.models import Plan

# usage_type -> monthly_usage column is 1:1; whitelist lives in usage_service
PLAN_LIMITS: dict[Plan, dict[str, int | None]] = {
    Plan.TRIAL: {
        "posts_generated": 10,
        "images_generated": 5,
        "ai_messages": 50,
        "leads_captured": 25,
    },
    Plan.STARTER: {
        "posts_generated": 60,
        "images_generated": 60,
        "ai_messages": 1000,
        "leads_captured": 500,
    },
    Plan.GROWTH: {
        "posts_generated": 240,
        "images_generated": 240,
        "ai_messages": 5000,
        "leads_captured": 2500,
    },
    Plan.AGENCY: {
        "posts_generated": None,
        "images_generated": None,
        "ai_messages": None,
        "leads_captured": None,
    },
}

NEXT_PLAN: dict[Plan, Plan | None] = {
    Plan.TRIAL: Plan.STARTER,
    Plan.STARTER: Plan.GROWTH,
    Plan.GROWTH: Plan.AGENCY,
    Plan.AGENCY: None,
}

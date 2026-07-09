/**
 * Platform-wide constants: plans, limits, business categories, social
 * platforms, Celery queue names. Compiled into the frontend bundle — never
 * put secrets here.
 */

export const PLANS = ["trial", "starter", "growth", "agency"] as const;
export type Plan = (typeof PLANS)[number];

/** Monthly price in paise (integers only — never floats for money). */
export const PLAN_PRICES_PAISE: Record<Plan, number> = {
  trial: 0,
  starter: 2_999_00,
  growth: 6_999_00,
  agency: 14_999_00,
};

export const SOCIAL_PLATFORMS = [
  "meta",
  "instagram",
  "whatsapp",
  "tiktok",
  "linkedin",
] as const;
export type SocialPlatform = (typeof SOCIAL_PLATFORMS)[number];

export const BUSINESS_CATEGORIES = [
  "home_cleaning",
  "plumbing",
  "electrical",
  "wedding_photography",
  "interior_design",
  "personal_training",
  "salon_beauty",
  "pet_care",
  "tutoring",
  "catering",
  "event_planning",
  "ac_appliance_repair",
  "pest_control",
  "physiotherapy",
  "yoga_wellness",
  "landscaping",
] as const;
export type BusinessCategory = (typeof BUSINESS_CATEGORIES)[number];

export const CELERY_QUEUES = [
  "ai_conversations",
  "post_publishing",
  "creative_generation",
  "lead_outreach",
  "ad_management",
  "usage_tracking",
] as const;

/** Local development port assignments (documented in CONTRIBUTING.md). */
export const DEV_PORTS = {
  api: 8000,
  web: 3000,
  postgres: 5432,
  redis: 6379,
  flower: 5555,
} as const;

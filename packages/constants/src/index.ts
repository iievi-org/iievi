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

/**
 * Monthly usage quotas per plan; null = unlimited.
 * Mirror of apps/api/app/core/plans.py PLAN_LIMITS — keep in sync.
 */
export const PLAN_LIMITS: Record<
  Plan,
  Record<"posts_generated" | "images_generated" | "ai_messages" | "leads_captured", number | null>
> = {
  trial: { posts_generated: 10, images_generated: 5, ai_messages: 50, leads_captured: 25 },
  starter: {
    posts_generated: 60,
    images_generated: 60,
    ai_messages: 1000,
    leads_captured: 500,
  },
  growth: {
    posts_generated: 240,
    images_generated: 240,
    ai_messages: 5000,
    leads_captured: 2500,
  },
  agency: {
    posts_generated: null,
    images_generated: null,
    ai_messages: null,
    leads_captured: null,
  },
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

/**
 * Feature keys exposed by GET /billing/capabilities (the `can_*` booleans).
 * `useCapabilities().hasFeature(name)` checks these; keep in sync with the
 * Capabilities interface in @iievi/types.
 */
export const FEATURES = [
  "can_generate_posts",
  "can_create_ads",
  "can_publish_tiktok",
  "can_publish_linkedin",
  "can_use_ai_conversations",
] as const;
export type FeatureName = (typeof FEATURES)[number];

/**
 * Realtime event types emitted over the tenant WebSocket channel. Mirror of
 * apps/api/app/modules/realtime/events.py EventType — keep in sync.
 */
export const WS_EVENT_TYPES = [
  "new_lead",
  "lead_status_changed",
  "ai_typing_started",
  "ai_response_sent",
  "new_message",
  "lead_handed_off",
  "notification_count_changed",
  "post_generated",
  "post_published",
  "post_failed",
] as const;
export type WsEventType = (typeof WS_EVENT_TYPES)[number];

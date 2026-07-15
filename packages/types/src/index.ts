/**
 * Shared API types — the single source of truth for every response shape the
 * backend produces, consumed by web (and the future React Native app). Enum
 * unions that have a runtime counterpart live in @iievi/constants and are
 * re-exported here so there is exactly one source and no drift.
 *
 * Every enum value MUST match the Python backend's StrEnum values verbatim
 * (apps/api/app/db/models.py) — a mismatch causes silent validation failures.
 */

import type { BusinessCategory, Plan, SocialPlatform, WsEventType } from "@iievi/constants";

export type {
  BusinessCategory,
  FeatureName,
  Plan,
  SocialPlatform,
  WsEventType,
} from "@iievi/constants";

/** The backend `Platform` enum is the same set as SocialPlatform. */
export type Platform = SocialPlatform;

// ---------------------------------------------------------------------------
// Enum unions (mirror apps/api/app/db/models.py)
// ---------------------------------------------------------------------------

export type TenantStatus = "active" | "suspended" | "cancelled";
export type UserRole = "owner" | "admin" | "member";
export type LeadSource =
  | "comment"
  | "direct_message"
  | "whatsapp"
  | "story_reply"
  | "ad_click"
  | "manual";
export type LeadStatus = "new" | "engaged" | "qualified" | "booked" | "won" | "lost";
export type ConversationRole = "lead" | "assistant" | "human_agent" | "system";
export type ConversationState =
  | "new"
  | "greeted"
  | "qualifying"
  | "pitch_sent"
  | "booking_offered"
  | "booked"
  | "handed_off"
  | "lost";
export type PostStatus = "draft" | "scheduled" | "publishing" | "published" | "failed";
export type SubscriptionStatus = "trialing" | "active" | "past_due" | "paused" | "cancelled";
export type NotificationType =
  | "new_lead"
  | "post_published"
  | "post_failed"
  | "payment_failed"
  | "credential_expired"
  | "ai_handoff"
  | "weekly_summary";
export type AuditAction =
  | "create"
  | "update"
  | "delete"
  | "login"
  | "logout"
  | "credential_access"
  | "plan_change"
  | "suspension";

/** JSONB blobs the backend stores untyped; the frontend narrows at the edge. */
export type JsonObject = Record<string, unknown>;

// ---------------------------------------------------------------------------
// Error envelope + health
// ---------------------------------------------------------------------------

/** Error envelope returned by every non-2xx API response. */
export interface ApiError {
  code: string;
  message: string;
  details: JsonObject;
}

export interface HealthResponse {
  status: "ok";
  version: string;
  commit: string;
  uptime_seconds: number;
}

export interface DependencyStatus {
  healthy: boolean;
  detail: string;
}

export interface DeepHealthResponse {
  status: "ok" | "degraded";
  database: DependencyStatus;
  redis: DependencyStatus;
  celery: DependencyStatus;
}

export interface VersionResponse {
  commit: string;
  deployed_at: string;
  version: string;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

/** POST /auth/register | /auth/login | /auth/refresh */
export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

/** Claims inside the access-token JWT (read client-side, verified server-side). */
export interface JwtClaims {
  sub: string; // user id
  tid: string; // tenant id
  plan: Plan;
  role: UserRole;
  admin: boolean;
  jti: string;
  iat: number;
  exp: number;
  type: "access";
}

/** The current user, derived from the decoded access token. */
export interface AuthUser {
  userId: string;
  tenantId: string;
  plan: Plan;
  role: UserRole;
  isAdmin: boolean;
}

/** GET /auth/ws-token */
export interface WsTokenResponse {
  token: string;
  expires_in: number;
}

// ---------------------------------------------------------------------------
// Tenant
// ---------------------------------------------------------------------------

export interface Tenant {
  id: string;
  name: string;
  status: TenantStatus;
  plan: Plan;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Profile
// ---------------------------------------------------------------------------

export interface ServiceItem {
  name: string;
  price_min_paise: number;
  price_max_paise: number;
  unit: string;
}

export interface BusinessProfile {
  category: BusinessCategory;
  business_name: string;
  description: string | null;
  services: { items: ServiceItem[] };
  pricing: JsonObject;
  hours: JsonObject;
  locations: JsonObject;
  faqs: JsonObject;
  policies: JsonObject;
  booking_url?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
}

export interface CustomerPersona {
  name: string;
  description: string;
  attributes: JsonObject;
}

export interface CompetitorAnalysis {
  competitor_name: string;
  data: JsonObject;
}

export interface MarketingConfig {
  tone: string | null;
  goals: JsonObject;
  posting_schedule: JsonObject;
  target_audience: JsonObject;
}

export interface BrandKit {
  colors: JsonObject;
  fonts: JsonObject;
  logo_url: string | null;
}

/** GET /profiles — assembled across six tables. */
export interface ProfileAssembly {
  business_profile: BusinessProfile | null;
  customer_personas: CustomerPersona[];
  competitor_analysis: CompetitorAnalysis[];
  marketing_config: MarketingConfig | null;
  brand_kit: BrandKit | null;
}

/** GET /profiles/completeness */
export interface ProfileCompleteness {
  percentage: number;
  incomplete_sections: string[];
}

// ---------------------------------------------------------------------------
// Onboarding (12-stage conversational state machine)
// ---------------------------------------------------------------------------

export type OnboardingStage =
  | "welcome"
  | "category_select"
  | "business_info"
  | "business_overview"
  | "target_audience"
  | "existing_customers"
  | "competitor_analysis"
  | "brand_identity"
  | "creative_preferences"
  | "marketing_goals"
  | "lead_management"
  | "confirm_and_create";

/** POST /onboarding/message — one conversational turn. */
export interface OnboardingTurnResponse {
  stage: OnboardingStage;
  reply: string;
  /** True when this turn completed the current stage and advanced. */
  advanced: boolean;
  /** True only at confirm_and_create once the profile is materialised. */
  completed?: boolean;
  /** True when the user must register/login to proceed (confirm stage). */
  requires_auth?: boolean;
}

// ---------------------------------------------------------------------------
// Leads + conversations
// ---------------------------------------------------------------------------

export interface Lead {
  id: string;
  source: LeadSource;
  status: LeadStatus;
  platform: Platform;
  platform_id: string;
  name: string | null;
  phone: string | null;
  email: string | null;
  manual_mode: boolean;
  last_inbound_at: string | null;
  metadata: JsonObject;
  created_at: string;
  updated_at: string;
  conversation_state?: ConversationState;
}

/** GET /leads — cursor paginated ({updated_at}:{lead_id}). */
export interface LeadListResponse {
  leads: Lead[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface ConversationMessage {
  id: string;
  role: ConversationRole;
  content: string;
  created_at: string;
}

/** GET /leads/{id}/conversation */
export interface ConversationHistory {
  lead_id: string;
  messages: ConversationMessage[];
}

// ---------------------------------------------------------------------------
// Posts
// ---------------------------------------------------------------------------

export interface Post {
  id: string;
  status: PostStatus;
  platforms: JsonObject;
  content: string | null;
  media_urls: JsonObject;
  scheduled_at: string | null;
  published_at: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

/** POST /posts/generate */
export interface GeneratePostResponse {
  post_id: string;
  chain_task_id: string;
  status: "queued";
}

/** GET /posts/{id}/progress */
export interface PostProgress {
  post_id: string;
  stage: PostStatus;
}

// ---------------------------------------------------------------------------
// Billing / capabilities
// ---------------------------------------------------------------------------

export interface UsageLimits {
  posts_generated: number | null;
  images_generated: number | null;
  ai_messages: number | null;
  leads_captured: number | null;
}

export interface UsageStatus {
  posts_generated: number;
  images_generated: number;
  ai_messages: number;
  leads_captured: number;
  limits: UsageLimits;
}

/** GET /billing/capabilities — the single source of truth for feature gates. */
export interface Capabilities {
  can_generate_posts: boolean;
  can_create_ads: boolean;
  can_publish_tiktok: boolean;
  can_publish_linkedin: boolean;
  can_use_ai_conversations: boolean;
  is_suspended: boolean;
  plan: Plan;
  usage: UsageStatus;
}

export interface Subscription {
  id: string;
  plan: Plan;
  status: SubscriptionStatus;
  provider: string;
  amount_paise: number;
  currency: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  action_url: string | null;
  read_at: string | null;
  created_at: string;
}

/** GET /notifications */
export interface NotificationListResponse {
  notifications: Notification[];
  next_cursor: string | null;
  has_more: boolean;
  unread: number;
}

export interface NotificationPreferences {
  email_enabled: boolean;
  whatsapp_enabled: boolean;
  in_app_enabled: boolean;
  overrides: Record<string, Record<string, boolean>>;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  quiet_hours_days: number[];
}

// ---------------------------------------------------------------------------
// Credentials
// ---------------------------------------------------------------------------

export interface ConnectedCredential {
  service: string;
  last_used_at: string | null;
}

/** GET /credentials */
export interface CredentialsResponse {
  connected: ConnectedCredential[];
  available: string[];
}

// ---------------------------------------------------------------------------
// Analytics + audit
// ---------------------------------------------------------------------------

/**
 * GET /analytics/summary. Field set is provisional — align with the analytics
 * router when its shape is finalised; extra keys are tolerated by the parser.
 */
export interface AnalyticsSummary {
  period: string;
  leads_received: number;
  leads_converted: number;
  conversion_rate: number;
  posts_published: number;
  ai_messages: number;
  bookings: number;
}

/** One row from GET /admin/logs (structured JSON log lines). */
export interface AuditLogEntry {
  timestamp?: string;
  level?: string;
  module?: string;
  message?: string;
  tenant_id?: string | null;
  request_id?: string | null;
  [key: string]: unknown;
}

/** GET /admin/logs — Axiom-backed log query result. */
export interface AdminLogsResponse {
  logs: AuditLogEntry[];
  count: number;
  query: {
    tenant_id: string | null;
    from_date: string;
    to_date: string;
    level: string | null;
  };
}

/** GET /admin/feature-flags — one flag (FlagOut). */
export interface FeatureFlag {
  flag_key: string;
  description: string | null;
  enabled_globally: boolean;
  enabled_for_tenants: string[];
  disabled_for_tenants: string[];
  minimum_plan: Plan | null;
}

// ---------------------------------------------------------------------------
// WebSocket events ({type, data} envelope)
// ---------------------------------------------------------------------------

/** Non-backend event: the frontend's own "update available" banner trigger. */
export type FrontendWsEventType = "deployment_notification";

export interface WsMessage {
  type: WsEventType | FrontendWsEventType;
  data: JsonObject;
}

export interface NewLeadEventData {
  lead_id: string;
  name?: string;
  platform?: Platform;
  reason?: string;
  preview?: string;
}

export interface LeadStatusChangedEventData {
  lead_id: string;
  status: LeadStatus;
}

export interface AiTypingEventData {
  lead_id: string;
}

export interface NotificationCountEventData {
  user_id: string;
  unread: number;
}

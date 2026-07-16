/**
 * Typed API client for the IIEVI backend. `createApiClient(options)` returns
 * domain-grouped modules (auth, profiles, leads, posts, billing, notifications,
 * analytics) with an explicit TypeScript return type on every method. Portable
 * to React Native — only the fetch standard is used; auth/CSRF/refresh are
 * supplied by the host via callbacks (see ApiClientOptions in ./base).
 */

import type {
  AdminLogsResponse,
  Capabilities,
  ConversationHistory,
  CredentialsResponse,
  DeepHealthResponse,
  FeatureFlag,
  GeneratePostResponse,
  HealthResponse,
  Lead,
  LeadListResponse,
  LeadSource,
  LeadStatus,
  NotificationListResponse,
  NotificationPreferences,
  OnboardingTurnResponse,
  Plan,
  Platform,
  PostProgress,
  PostStatus,
  ProfileAssembly,
  ProfileCompleteness,
  ServiceItem,
  TokenResponse,
  VersionResponse,
  WsTokenResponse,
} from "@iievi/types";
import type { LoginInput, RegisterInput } from "@iievi/validators";
import { tokenResponseSchema, wsTokenResponseSchema } from "@iievi/validators";
import type { ZodType } from "zod";

import { apiRequest, type ApiClientOptions, type RequestInitLite } from "./base";

export * from "./base";

// ---------------------------------------------------------------------------
// Request param / body types
// ---------------------------------------------------------------------------

export interface LeadListParams {
  status?: LeadStatus;
  source?: LeadSource;
  created_after?: string;
  created_before?: string;
  cursor?: string;
  limit?: number;
}

export interface PageParams {
  cursor?: string;
  limit?: number;
}

export interface GeneratePostBody {
  platform: "instagram" | "facebook" | "linkedin" | "tiktok";
  topic: string;
  format?: "square" | "portrait" | "story" | "landscape";
  scheduled_at?: string;
}

export interface LeadPatchBody {
  status?: LeadStatus;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
}

/** Free-form profile update; the backend validates each provided field. */
export type ProfileUpdateBody = Record<string, unknown>;

export type NotificationPreferencesUpdate = Partial<NotificationPreferences>;

/** POST /analytics/onboarding-event — onboarding funnel telemetry. */
export interface OnboardingEventBody {
  session_token: string;
  stage: string;
  event_type: string;
  metadata?: Record<string, unknown>;
}

export interface AdminLogsParams {
  tenant_id?: string;
  from_date?: string;
  to_date?: string;
  level?: string;
  limit?: number;
}

export interface FlagCreateBody {
  flag_key: string;
  description?: string;
  enabled_globally?: boolean;
  minimum_plan?: Plan | null;
}

export interface FlagPatchBody {
  description?: string | null;
  enabled_globally?: boolean | null;
  minimum_plan?: Plan | null;
  add_enabled_tenants?: string[];
  remove_enabled_tenants?: string[];
  add_disabled_tenants?: string[];
  remove_disabled_tenants?: string[];
}

// ---------------------------------------------------------------------------
// Query-string helper
// ---------------------------------------------------------------------------

function qs(params?: object): string {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

function body(value: unknown): RequestInitLite {
  return { body: JSON.stringify(value) };
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

export function createApiClient(options: ApiClientOptions) {
  const req = <T>(path: string, init: RequestInitLite = {}, schema?: ZodType<T>): Promise<T> =>
    apiRequest<T>(options, path, init, schema);

  return {
    health: {
      get: (): Promise<HealthResponse> => req<HealthResponse>("/health"),
      version: (): Promise<VersionResponse> => req<VersionResponse>("/health/version"),
      deep: (healthKey: string): Promise<DeepHealthResponse> =>
        req<DeepHealthResponse>("/health/deep", { headers: { "X-Health-Key": healthKey } }),
    },

    auth: {
      register: (input: RegisterInput): Promise<TokenResponse> =>
        req<TokenResponse>(
          "/api/v1/auth/register",
          { method: "POST", ...body(input) },
          tokenResponseSchema,
        ),
      login: (input: LoginInput): Promise<TokenResponse> =>
        req<TokenResponse>(
          "/api/v1/auth/login",
          { method: "POST", ...body(input) },
          tokenResponseSchema,
        ),
      refresh: (): Promise<TokenResponse> =>
        req<TokenResponse>("/api/v1/auth/refresh", { method: "POST" }, tokenResponseSchema),
      logout: (): Promise<void> => req<void>("/api/v1/auth/logout", { method: "POST" }),
      wsToken: (): Promise<WsTokenResponse> =>
        req<WsTokenResponse>("/api/v1/auth/ws-token", {}, wsTokenResponseSchema),
    },

    profiles: {
      get: (): Promise<ProfileAssembly> => req<ProfileAssembly>("/api/v1/profiles"),
      update: (payload: ProfileUpdateBody): Promise<{ updated: string[] }> =>
        req<{ updated: string[] }>("/api/v1/profiles", { method: "PUT", ...body(payload) }),
      addService: (item: ServiceItem): Promise<{ services: ServiceItem[] }> =>
        req<{ services: ServiceItem[] }>("/api/v1/profiles/services", {
          method: "POST",
          ...body(item),
        }),
      deleteService: (index: number): Promise<{ services: ServiceItem[] }> =>
        req<{ services: ServiceItem[] }>(`/api/v1/profiles/services/${index}`, {
          method: "DELETE",
        }),
      completeness: (): Promise<ProfileCompleteness> =>
        req<ProfileCompleteness>("/api/v1/profiles/completeness"),
    },

    leads: {
      list: (params?: LeadListParams): Promise<LeadListResponse> =>
        req<LeadListResponse>(`/api/v1/leads${qs(params)}`),
      get: (leadId: string): Promise<Lead> => req<Lead>(`/api/v1/leads/${leadId}`),
      conversation: (leadId: string): Promise<ConversationHistory> =>
        req<ConversationHistory>(`/api/v1/leads/${leadId}/conversation`),
      patch: (leadId: string, payload: LeadPatchBody): Promise<Lead> =>
        req<Lead>(`/api/v1/leads/${leadId}`, { method: "PATCH", ...body(payload) }),
      takeOver: (leadId: string): Promise<Lead> =>
        req<Lead>(`/api/v1/leads/${leadId}/take-over`, { method: "PATCH" }),
      resumeAi: (leadId: string): Promise<Lead> =>
        req<Lead>(`/api/v1/leads/${leadId}/resume-ai`, { method: "PATCH" }),
      sendMessage: (leadId: string, text: string): Promise<{ sent: boolean }> =>
        req<{ sent: boolean }>(`/api/v1/leads/${leadId}/message`, {
          method: "POST",
          ...body({ text }),
        }),
    },

    posts: {
      generate: (payload: GeneratePostBody): Promise<GeneratePostResponse> =>
        req<GeneratePostResponse>("/api/v1/posts/generate", { method: "POST", ...body(payload) }),
      progress: (postId: string): Promise<PostProgress> =>
        req<PostProgress>(`/api/v1/posts/${postId}/progress`),
    },

    billing: {
      capabilities: (): Promise<Capabilities> => req<Capabilities>("/api/v1/billing/capabilities"),
    },

    credentials: {
      list: (): Promise<CredentialsResponse> => req<CredentialsResponse>("/api/v1/credentials"),
      connect: (service: string, data: Record<string, string>): Promise<{ service: string; verified: boolean }> =>
        req<{ service: string; verified: boolean }>("/api/v1/credentials", {
          method: "POST",
          ...body({ service, data }),
        }),
      disconnect: (service: string): Promise<void> =>
        req<void>(`/api/v1/credentials/${service}`, { method: "DELETE" }),
    },

    notifications: {
      list: (params?: PageParams): Promise<NotificationListResponse> =>
        req<NotificationListResponse>(`/api/v1/notifications${qs(params)}`),
      markRead: (notificationId: string): Promise<{ read: boolean }> =>
        req<{ read: boolean }>(`/api/v1/notifications/${notificationId}/read`, { method: "PATCH" }),
      markAllRead: (): Promise<{ marked: number }> =>
        req<{ marked: number }>("/api/v1/notifications/read-all", { method: "PATCH" }),
      updatePreferences: (payload: NotificationPreferencesUpdate): Promise<{ updated: string[] }> =>
        req<{ updated: string[] }>("/api/v1/users/notification-preferences", {
          method: "PATCH",
          ...body(payload),
        }),
    },

    onboarding: {
      message: (message: string): Promise<OnboardingTurnResponse> =>
        req<OnboardingTurnResponse>("/api/v1/onboarding/message", {
          method: "POST",
          ...body({ message }),
        }),
      /** Onboarding funnel telemetry (fire-and-forget). */
      trackEvent: (payload: OnboardingEventBody): Promise<void> =>
        req<void>("/api/v1/analytics/onboarding-event", { method: "POST", ...body(payload) }),
    },

    admin: {
      logs: (params?: AdminLogsParams): Promise<AdminLogsResponse> =>
        req<AdminLogsResponse>(`/api/v1/admin/logs${qs(params)}`),
      flags: {
        list: (): Promise<FeatureFlag[]> => req<FeatureFlag[]>("/api/v1/admin/feature-flags"),
        create: (payload: FlagCreateBody): Promise<FeatureFlag> =>
          req<FeatureFlag>("/api/v1/admin/feature-flags", { method: "POST", ...body(payload) }),
        patch: (key: string, payload: FlagPatchBody): Promise<FeatureFlag> =>
          req<FeatureFlag>(`/api/v1/admin/feature-flags/${key}`, {
            method: "PATCH",
            ...body(payload),
          }),
        remove: (key: string): Promise<void> =>
          req<void>(`/api/v1/admin/feature-flags/${key}`, { method: "DELETE" }),
      },
    },
  };
}

/** The typed client returned by {@link createApiClient}. */
export type ApiClient = ReturnType<typeof createApiClient>;

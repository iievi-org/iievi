/**
 * Shared API types. Every response shape the backend produces is defined here
 * so web (and the future React Native app) consume one source of truth.
 */

/** Error envelope returned by every non-2xx API response. */
export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

/** GET /health */
export interface HealthResponse {
  status: "ok";
  version: string;
  commit: string;
  uptime_seconds: number;
}

/** One dependency inside GET /health/deep */
export interface DependencyStatus {
  healthy: boolean;
  detail: string;
}

/** GET /health/deep */
export interface DeepHealthResponse {
  status: "ok" | "degraded";
  database: DependencyStatus;
  redis: DependencyStatus;
  celery: DependencyStatus;
}

/** GET /health/version */
export interface VersionResponse {
  commit: string;
  deployed_at: string;
  version: string;
}

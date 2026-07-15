/**
 * Core request primitive for the typed API client. Uses only the fetch
 * standard (portable to React Native) and never touches the DOM directly —
 * the host app supplies the token / CSRF / refresh behaviour via callbacks.
 *
 * Responsibilities:
 * - prepend baseUrl, send Accept/Content-Type JSON
 * - attach `Authorization: Bearer <token>` from the in-memory token getter
 * - attach `X-CSRF-Token` (from the CSRF cookie getter) on state-changing verbs
 * - on 401, trigger the refresh callback once and retry the original request
 * - map the backend `{code, message, details}` envelope to typed error classes
 */

import type { ZodType } from "zod";

const STATE_CHANGING = new Set(["POST", "PUT", "PATCH", "DELETE"]);

// ---------------------------------------------------------------------------
// Typed errors
// ---------------------------------------------------------------------------

/** Base error for any non-2xx response. Subclasses select on HTTP status. */
export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown>) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/** 401 — missing/expired/invalid token; refresh has already been attempted. */
export class AuthError extends ApiRequestError {
  constructor(code: string, message: string, details: Record<string, unknown>) {
    super(401, code, message, details);
    this.name = "AuthError";
  }
}

/** 402 — a plan/usage limit was reached. `details` carries upgrade info. */
export class PlanLimitError extends ApiRequestError {
  constructor(code: string, message: string, details: Record<string, unknown>) {
    super(402, code, message, details);
    this.name = "PlanLimitError";
  }
}

/** 403 — permission denied or CSRF failure. */
export class ForbiddenError extends ApiRequestError {
  constructor(code: string, message: string, details: Record<string, unknown>) {
    super(403, code, message, details);
    this.name = "ForbiddenError";
  }
}

/** 404 — the resource does not exist. Components render an empty state. */
export class NotFoundError extends ApiRequestError {
  constructor(code: string, message: string, details: Record<string, unknown>) {
    super(404, code, message, details);
    this.name = "NotFoundError";
  }
}

/** 409 — a state-machine / conflict violation. */
export class ConflictError extends ApiRequestError {
  constructor(code: string, message: string, details: Record<string, unknown>) {
    super(409, code, message, details);
    this.name = "ConflictError";
  }
}

/** 422 — request validation failed. `details.errors` lists field errors. */
export class ValidationError extends ApiRequestError {
  constructor(code: string, message: string, details: Record<string, unknown>) {
    super(422, code, message, details);
    this.name = "ValidationError";
  }
}

/** 429 — rate limited. */
export class RateLimitError extends ApiRequestError {
  constructor(code: string, message: string, details: Record<string, unknown>) {
    super(429, code, message, details);
    this.name = "RateLimitError";
  }
}

function makeError(
  status: number,
  code: string,
  message: string,
  details: Record<string, unknown>,
): ApiRequestError {
  switch (status) {
    case 401:
      return new AuthError(code, message, details);
    case 402:
      return new PlanLimitError(code, message, details);
    case 403:
      return new ForbiddenError(code, message, details);
    case 404:
      return new NotFoundError(code, message, details);
    case 409:
      return new ConflictError(code, message, details);
    case 422:
      return new ValidationError(code, message, details);
    case 429:
      return new RateLimitError(code, message, details);
    default:
      return new ApiRequestError(status, code, message, details);
  }
}

function errorFromBody(status: number, body: unknown, fallback: string): ApiRequestError {
  // FastAPI sometimes wraps our envelope inside `{ detail: {...} }`.
  const envelope =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail: unknown }).detail
      : body;
  if (envelope && typeof envelope === "object") {
    const e = envelope as Record<string, unknown>;
    const code = typeof e.code === "string" ? e.code : "unknown_error";
    const message = typeof e.message === "string" ? e.message : fallback;
    const details =
      e.details && typeof e.details === "object" ? (e.details as Record<string, unknown>) : {};
    return makeError(status, code, message, details);
  }
  return makeError(status, "unknown_error", fallback || "Request failed", {});
}

// ---------------------------------------------------------------------------
// Client options + request
// ---------------------------------------------------------------------------

export interface ApiClientOptions {
  /** e.g. https://api.iievi.app — NEXT_PUBLIC_API_URL on the web. */
  baseUrl: string;
  /** Current in-memory access token, or null when unauthenticated. */
  getAccessToken?: () => string | null;
  /** CSRF token read from the csrf_token cookie (state-changing requests). */
  getCsrfToken?: () => string | null;
  /**
   * Attempt a token refresh. Return true if a fresh access token is now
   * available. Invoked at most once per request when a 401 is received.
   */
  refresh?: () => Promise<boolean>;
  /** Called when authentication is unrecoverable (refresh failed). */
  onAuthFailure?: () => void;
}

export interface RequestInitLite {
  method?: string;
  body?: string;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

/**
 * Perform one API request. When `schema` is provided the response body is
 * validated (used for security-critical shapes); otherwise it is returned as
 * the declared type `T`.
 */
export async function apiRequest<T>(
  options: ApiClientOptions,
  path: string,
  init: RequestInitLite = {},
  schema?: ZodType<T>,
): Promise<T> {
  const isRefreshCall = path.startsWith("/api/v1/auth/refresh");

  const send = (): Promise<Response> => {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (init.body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const token = options.getAccessToken?.();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    const method = (init.method ?? "GET").toUpperCase();
    if (STATE_CHANGING.has(method)) {
      const csrf = options.getCsrfToken?.();
      if (csrf) headers.set("X-CSRF-Token", csrf);
    }
    // Build RequestInit without setting undefined keys (exactOptionalPropertyTypes).
    const requestInit: RequestInit = { headers, credentials: "include" };
    if (init.method !== undefined) requestInit.method = init.method;
    if (init.body !== undefined) requestInit.body = init.body;
    if (init.signal !== undefined) requestInit.signal = init.signal;
    return fetch(`${options.baseUrl}${path}`, requestInit);
  };

  let response = await send();

  // 401 → refresh once → retry the original request exactly once.
  if (response.status === 401 && options.refresh && !isRefreshCall) {
    const refreshed = await options.refresh();
    if (refreshed) {
      response = await send();
    } else {
      options.onAuthFailure?.();
    }
  }

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      /* error responses without a JSON body fall back to statusText */
    }
    throw errorFromBody(response.status, body, response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  const data: unknown = await response.json();
  return schema ? schema.parse(data) : (data as T);
}

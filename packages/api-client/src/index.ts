/**
 * Typed API client. Every function validates the response body with the
 * matching Zod schema before returning, so callers never receive an
 * unexpected shape. Uses only the fetch standard — portable to React Native.
 */

import type { DeepHealthResponse, HealthResponse, VersionResponse } from "@iievi/types";
import {
  apiErrorSchema,
  deepHealthResponseSchema,
  healthResponseSchema,
  versionResponseSchema,
} from "@iievi/validators";
import type { z } from "zod";

/** Typed error thrown for any non-2xx response. */
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

export interface ApiClientOptions {
  baseUrl: string;
  /** Returns the current access token, or null when unauthenticated. */
  getAccessToken?: () => string | null;
}

async function request<T>(
  options: ApiClientOptions,
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  const token = options.getAccessToken?.();
  if (token !== null && token !== undefined) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${options.baseUrl}${path}`, { ...init, headers });
  const body: unknown = await response.json();
  if (!response.ok) {
    const parsed = apiErrorSchema.safeParse(
      typeof body === "object" && body !== null && "detail" in body
        ? (body as { detail: unknown }).detail
        : body,
    );
    if (parsed.success) {
      throw new ApiRequestError(
        response.status,
        parsed.data.code,
        parsed.data.message,
        parsed.data.details,
      );
    }
    throw new ApiRequestError(response.status, "unknown_error", response.statusText, {});
  }
  return schema.parse(body);
}

export function getHealth(options: ApiClientOptions): Promise<HealthResponse> {
  return request(options, "/health", healthResponseSchema);
}

export function getDeepHealth(
  options: ApiClientOptions,
  healthKey: string,
): Promise<DeepHealthResponse> {
  return request(options, "/health/deep", deepHealthResponseSchema, {
    headers: { "X-Health-Key": healthKey },
  });
}

export function getVersion(options: ApiClientOptions): Promise<VersionResponse> {
  return request(options, "/health/version", versionResponseSchema);
}

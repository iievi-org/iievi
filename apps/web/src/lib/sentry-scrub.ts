/**
 * Sentry credential scrubbing — mirrors apps/api/app/core/sentry.py exactly.
 * Any field named like a credential is redacted before the event leaves the
 * browser or server. Security requirement with no exceptions.
 */

import type { ErrorEvent } from "@sentry/nextjs";

const SENSITIVE_KEYS = new Set([
  "api_key",
  "apikey",
  "token",
  "access_token",
  "refresh_token",
  "password",
  "encrypted_key",
  "encrypted_token",
  "secret",
  "authorization",
  "cookie",
]);

const REDACTED = "[REDACTED]";

function scrubValue(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(scrubValue);
  }
  if (value !== null && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, inner] of Object.entries(value)) {
      result[key] = SENSITIVE_KEYS.has(key.toLowerCase()) ? REDACTED : scrubValue(inner);
    }
    return result;
  }
  return value;
}

export function scrubEvent(event: ErrorEvent): ErrorEvent {
  return scrubValue(event) as ErrorEvent;
}

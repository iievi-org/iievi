/**
 * The app-wide API client instance, wired to the in-memory token store, the CSRF
 * cookie reader, and a de-duplicated token-refresh flow. Every data hook and
 * mutation goes through `api`.
 */

import { createApiClient } from "@iievi/api-client";

import { clearAccessToken, getAccessToken, setAccessToken } from "./auth-state";
import { readCsrfToken } from "./csrf";
import { triggerAuthFailure } from "./ui-events";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let refreshInFlight: Promise<boolean> | null = null;

async function doRefresh(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return false;
    const data = (await response.json()) as { access_token?: unknown };
    if (typeof data.access_token === "string") {
      setAccessToken(data.access_token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

/** Exchange the refresh cookie for a new access token, de-duping concurrent calls. */
export function refreshAccessToken(): Promise<boolean> {
  refreshInFlight ??= doRefresh().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

export const api = createApiClient({
  baseUrl: API_BASE_URL,
  getAccessToken,
  getCsrfToken: readCsrfToken,
  refresh: refreshAccessToken,
  onAuthFailure: () => {
    clearAccessToken();
    triggerAuthFailure();
  },
});

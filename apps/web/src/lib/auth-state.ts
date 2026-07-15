/**
 * In-memory access-token store (Prompt 8 Step 7).
 *
 * The access token lives ONLY in this module-level variable — never in
 * localStorage (XSS-readable) and never in a cookie (CSRF surface). It is lost
 * on a full page reload, which is exactly why the app calls POST /auth/refresh
 * on mount to exchange the HttpOnly refresh cookie for a fresh access token.
 */

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function clearAccessToken(): void {
  accessToken = null;
}

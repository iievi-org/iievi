/**
 * Reads the JavaScript-readable `csrf_token` cookie so it can be echoed in the
 * `X-CSRF-Token` header on every state-changing request (the backend enforces a
 * synchronizer-token match). Returns null on the server or when absent.
 */
export function readCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  const value = match?.[1];
  return value ? decodeURIComponent(value) : null;
}

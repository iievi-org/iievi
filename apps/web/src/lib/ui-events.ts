/**
 * A tiny bridge for surfacing global API outcomes into React UI. The API client
 * and the TanStack Query error handler live outside the React tree, so they push
 * through these registered handlers, which providers wire up on mount.
 */

type UpgradeHandler = (details: Record<string, unknown>) => void;
type AuthFailureHandler = () => void;

let upgradeHandler: UpgradeHandler | null = null;
let authFailureHandler: AuthFailureHandler | null = null;

export function registerUpgradeHandler(handler: UpgradeHandler | null): void {
  upgradeHandler = handler;
}

/** Called on a 402 plan-limit response — opens the upgrade modal. */
export function triggerUpgrade(details: Record<string, unknown>): void {
  upgradeHandler?.(details);
}

export function registerAuthFailureHandler(handler: AuthFailureHandler | null): void {
  authFailureHandler = handler;
}

/** Called when a refresh fails — clears auth and redirects to login. */
export function triggerAuthFailure(): void {
  authFailureHandler?.();
}

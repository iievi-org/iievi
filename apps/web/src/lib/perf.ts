/**
 * Lightweight performance instrumentation (Step 13). Wraps the User Timing API
 * and forwards a custom metric to Vercel Analytics when it's present (a no-op
 * otherwise), so the chat/onboarding round-trip can be tracked in the field.
 * Target: under 8s from "user sends" to "AI reply visible".
 */

const ROUNDTRIP_TARGET_MS = 8000;

interface VercelAnalytics {
  (event: "event", name: string, data?: Record<string, unknown>): void;
}

export function mark(name: string): void {
  try {
    performance.mark(name);
  } catch {
    /* User Timing unavailable — ignore */
  }
}

/** Close a round-trip: stamp the end mark, measure from `startMark`, report it. */
export function measureRoundtrip(startMark: string, endMark: string, name: string): number | null {
  try {
    performance.mark(endMark);
    const measure = performance.measure(name, startMark, endMark);
    const duration = Math.round(measure.duration);
    const va = (globalThis as unknown as { va?: VercelAnalytics }).va;
    va?.("event", name, { value: duration, overBudget: duration > ROUNDTRIP_TARGET_MS });
    if (duration > ROUNDTRIP_TARGET_MS) {
      console.warn(`[perf] ${name} took ${duration}ms (over the ${ROUNDTRIP_TARGET_MS}ms target)`);
    }
    return duration;
  } catch {
    return null;
  }
}

/**
 * Reusable Framer Motion variants (Prompt 8 Step 8). Pair with <MotionWrapper>
 * for scroll-triggered entrances. All motion is disabled when the user has
 * `prefers-reduced-motion: reduce` (WCAG 2.1 AA) — see MotionWrapper and the
 * prefersReducedMotion() guard.
 */

import type { Variants } from "framer-motion";

/** Linen's signature easing curve. */
export const LINEN_EASE = [0.22, 1, 0.36, 1] as const;

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.4 } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  show: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: LINEN_EASE } },
};

export const staggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

/** Synchronous reduced-motion check for imperative animation code. */
export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

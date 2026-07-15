import { clsx, type ClassValue } from "clsx";

/**
 * Conditional class composition. We deliberately use clsx WITHOUT tailwind-merge:
 * Linen ships custom utilities (text-body-md, text-ink, bg-signal, …) that
 * tailwind-merge's default group heuristics would wrongly dedupe.
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

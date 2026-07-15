/**
 * Small pure helpers shared across the billing UI and the upgrade modal:
 * plan display labels, INR price formatting from paise, and usage-metric
 * labels. Kept free of React so both server- and client-side code can import.
 */

import { PLAN_PRICES_PAISE, type Plan } from "@iievi/constants";
import type { UsageLimits } from "@iievi/types";

export type UsageMetric = keyof UsageLimits;

/** Human labels for each plan (the raw values are lowercase enum strings). */
const PLAN_LABELS: Record<Plan, string> = {
  trial: "Trial",
  starter: "Starter",
  growth: "Growth",
  agency: "Agency",
};

/** One-line positioning copy per plan, used on the comparison cards. */
export const PLAN_TAGLINES: Record<Plan, string> = {
  trial: "Kick the tyres, free.",
  starter: "For a solo operator finding their rhythm.",
  growth: "For a busy business scaling output.",
  agency: "Unlimited everything, for teams.",
};

export function planLabel(plan: Plan): string {
  return PLAN_LABELS[plan];
}

/** Monthly price in whole rupees (paise ÷ 100). */
export function planPriceRupees(plan: Plan): number {
  return Math.round(PLAN_PRICES_PAISE[plan] / 100);
}

/** Formats a rupee amount with the Indian digit grouping, e.g. ₹2,999. */
export function formatRupees(rupees: number): string {
  return `₹${rupees.toLocaleString("en-IN")}`;
}

/** "Free" for ₹0, otherwise the grouped rupee price. */
export function formatPlanPrice(plan: Plan): string {
  const rupees = planPriceRupees(plan);
  return rupees === 0 ? "Free" : formatRupees(rupees);
}

/** Human labels for each usage metric surfaced on the billing page. */
export const METRIC_LABELS: Record<UsageMetric, string> = {
  posts_generated: "Posts generated",
  images_generated: "Images generated",
  ai_messages: "AI messages",
  leads_captured: "Leads captured",
};

/** The metrics rendered as usage bars / comparison rows, in display order. */
export const USAGE_METRICS: readonly UsageMetric[] = [
  "posts_generated",
  "images_generated",
  "ai_messages",
  "leads_captured",
] as const;

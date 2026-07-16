"use client";

import type { UsageLimits, UsageStatus } from "@iievi/types";

import { useCapabilities } from "./useCapabilities";

type UsageMetric = keyof UsageLimits;

export interface UsePlanLimitsResult {
  usage: UsageStatus | null;
  limits: UsageLimits | null;
  /** Remaining allowance for a metric; null = unlimited, undefined = unknown. */
  remaining: (metric: UsageMetric) => number | null | undefined;
  isAtLimit: (metric: UsageMetric) => boolean;
}

/** Current usage vs. plan limits, derived from GET /billing/capabilities. */
export function usePlanLimits(): UsePlanLimitsResult {
  const { capabilities } = useCapabilities();
  const usage = capabilities?.usage ?? null;
  const limits = usage?.limits ?? null;

  const remaining = (metric: UsageMetric): number | null | undefined => {
    if (!usage || !limits) return undefined;
    const limit = limits[metric];
    if (limit === null) return null; // unlimited
    return Math.max(limit - usage[metric], 0);
  };

  const isAtLimit = (metric: UsageMetric): boolean => {
    const left = remaining(metric);
    return typeof left === "number" && left <= 0;
  };

  return { usage, limits, remaining, isAtLimit };
}

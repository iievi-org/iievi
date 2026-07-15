"use client";

import type { Capabilities, FeatureName } from "@iievi/types";
import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface UseCapabilitiesResult {
  query: UseQueryResult<Capabilities>;
  capabilities: Capabilities | null;
  /** True when the plan grants the named feature (a `can_*` flag). */
  hasFeature: (feature: FeatureName) => boolean;
  isSuspended: boolean;
}

/**
 * Fetches GET /billing/capabilities (the single source of truth for feature
 * gates) with a 5-minute stale time. Every feature-gated UI element reads
 * `hasFeature`.
 */
export function useCapabilities(): UseCapabilitiesResult {
  const query = useQuery({
    queryKey: ["capabilities"],
    queryFn: () => api.billing.capabilities(),
    staleTime: 5 * 60 * 1000,
  });
  const capabilities = query.data ?? null;
  return {
    query,
    capabilities,
    hasFeature: (feature: FeatureName): boolean => (capabilities ? capabilities[feature] : false),
    isSuspended: capabilities?.is_suspended ?? false,
  };
}

"use client";

import type { ProfileAssembly } from "@iievi/types";
import { useQuery, type UseQueryResult } from "@tanstack/react-query";

import { api } from "@/lib/api";

/**
 * GET /profiles — the assembled business profile. 2-minute stale time (Step 13):
 * profile data changes rarely, so the sidebar/settings can read it cheaply.
 */
export function useProfile(): UseQueryResult<ProfileAssembly> {
  return useQuery({
    queryKey: ["profile"],
    queryFn: () => api.profiles.get(),
    staleTime: 2 * 60 * 1000,
  });
}

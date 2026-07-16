"use client";

import type { LeadListParams } from "@iievi/api-client";
import { useInfiniteQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface LeadsServerFilters {
  created_after?: string;
  created_before?: string;
}

/**
 * Cursor-paginated lead feed. Date range is applied server-side; status and
 * platform filtering happen client-side on the accumulated pages (the backend
 * filters by a single status/source, so multi-select is a client concern).
 * 30-second stale time (Step 13 — the inbox must stay fresh).
 */
export function useLeadsInfinite(server: LeadsServerFilters) {
  return useInfiniteQuery({
    queryKey: ["leads", server],
    queryFn: ({ pageParam }) => {
      const params: LeadListParams = { limit: 25 };
      if (server.created_after) params.created_after = server.created_after;
      if (server.created_before) params.created_before = server.created_before;
      if (pageParam) params.cursor = pageParam;
      return api.leads.list(params);
    },
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => (last.has_more ? (last.next_cursor ?? undefined) : undefined),
    staleTime: 30_000,
  });
}

/**
 * The TanStack Query client (Prompt 8 Step 6). Defaults: 60s stale, 5m gc,
 * single retry. A global query-error handler routes API failures:
 * - 402 plan-limit  -> open the upgrade modal (via the UI-event bus)
 * - 5xx / network   -> a Sonner toast (unexpected server errors)
 * 401 is handled by the API client's refresh interceptor; 404 surfaces as a
 * typed NotFoundError that components render as an empty state.
 */

import { ApiRequestError, PlanLimitError } from "@iievi/api-client";
import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { triggerUpgrade } from "./ui-events";

function handleError(error: unknown): void {
  if (error instanceof PlanLimitError) {
    triggerUpgrade(error.details);
    return;
  }
  if (error instanceof ApiRequestError) {
    // 401 (refresh), 402 (above), 404 (empty states) are handled elsewhere.
    if (error.status >= 500) {
      toast.error(error.message || "Something went wrong on our side. Please try again.");
    }
    return;
  }
  // Network / unexpected failures.
  toast.error("Network error — check your connection and try again.");
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 60_000, gcTime: 300_000, retry: 1, refetchOnWindowFocus: false },
      mutations: { retry: 0 },
    },
    queryCache: new QueryCache({ onError: handleError }),
    mutationCache: new MutationCache({ onError: handleError }),
  });
}

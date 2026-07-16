"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { clearAccessToken } from "@/lib/auth-state";

/**
 * Ends the session: revokes it server-side, drops the in-memory token, clears
 * cached queries (so the next user starts clean), and returns to /login.
 */
export function useLogout(): () => Promise<void> {
  const router = useRouter();
  const { setUser } = useAuth();
  const queryClient = useQueryClient();

  return useCallback(async () => {
    try {
      await api.auth.logout();
    } catch {
      // Even if the server call fails, tear down the client session.
    }
    clearAccessToken();
    setUser(null);
    queryClient.clear();
    router.replace("/login");
  }, [router, setUser, queryClient]);
}

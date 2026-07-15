"use client";

/**
 * Auth state + token management (Prompt 8 Step 7).
 *
 * The AuthProvider (mounted in the dashboard layout) exchanges the HttpOnly
 * refresh cookie for an access token on mount, on window focus, and on a timer
 * that fires 2 minutes before the JWT expires. The access token lives only in
 * the in-memory store (auth-state.ts); AuthContext exposes the decoded user.
 */

import type { AuthUser, JwtClaims } from "@iievi/types";
import { jwtDecode } from "jwt-decode";
import { useRouter } from "next/navigation";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

import { refreshAccessToken } from "./api";
import { clearAccessToken, getAccessToken } from "./auth-state";
import { registerAuthFailureHandler } from "./ui-events";

interface AuthContextValue {
  user: AuthUser | null;
  setUser: (user: AuthUser | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

/** Decode the in-memory access token into an AuthUser (no signature check). */
export function userFromToken(token: string | null): AuthUser | null {
  if (!token) return null;
  try {
    const claims = jwtDecode<JwtClaims>(token);
    return {
      userId: claims.sub,
      tenantId: claims.tid,
      plan: claims.plan,
      role: claims.role,
      isAdmin: claims.admin,
    };
  } catch {
    return null;
  }
}

const REFRESH_LEAD_MS = 2 * 60 * 1000; // refresh 2 min before expiry

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const router = useRouter();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scheduleRef = useRef<() => void>(() => undefined);

  const runRefresh = useCallback(async (): Promise<void> => {
    const ok = await refreshAccessToken();
    if (ok) {
      setUser(userFromToken(getAccessToken()));
      scheduleRef.current();
    } else {
      setUser(null);
    }
  }, []);

  const scheduleRefresh = useCallback((): void => {
    if (timerRef.current) clearTimeout(timerRef.current);
    const token = getAccessToken();
    if (!token) return;
    try {
      const { exp } = jwtDecode<JwtClaims>(token);
      const delay = Math.max(exp * 1000 - Date.now() - REFRESH_LEAD_MS, 1000);
      timerRef.current = setTimeout(() => void runRefresh(), delay);
    } catch {
      /* undecodable token — leave to the next focus/refresh */
    }
  }, [runRefresh]);

  useEffect(() => {
    scheduleRef.current = scheduleRefresh;
  }, [scheduleRefresh]);

  // Mount + window focus → refresh.
  useEffect(() => {
    void runRefresh();
    const onFocus = (): void => void runRefresh();
    window.addEventListener("focus", onFocus);
    return () => {
      window.removeEventListener("focus", onFocus);
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [runRefresh]);

  // Unrecoverable auth failure → clear + redirect to login.
  useEffect(() => {
    registerAuthFailureHandler(() => {
      clearAccessToken();
      setUser(null);
      router.replace("/login");
    });
    return () => registerAuthFailureHandler(null);
  }, [router]);

  return <AuthContext.Provider value={{ user, setUser }}>{children}</AuthContext.Provider>;
}

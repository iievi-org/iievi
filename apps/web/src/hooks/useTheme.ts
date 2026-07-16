"use client";

import { useCallback, useEffect, useState } from "react";

import { THEME_STORAGE_KEY as STORAGE_KEY } from "@/lib/theme";

export type Theme = "light" | "dark";

function readInitial(): Theme {
  if (typeof document === "undefined") return "light";
  const attr = document.documentElement.dataset.theme;
  return attr === "dark" ? "dark" : "light";
}

export function useTheme(): { theme: Theme; setTheme: (t: Theme) => void; toggle: () => void } {
  const [theme, setThemeState] = useState<Theme>(readInitial);

  useEffect(() => {
    const handler = (e: StorageEvent): void => {
      if (e.key === STORAGE_KEY && (e.newValue === "light" || e.newValue === "dark")) {
        setThemeState(e.newValue);
        document.documentElement.dataset.theme = e.newValue;
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);

  const setTheme = useCallback((next: Theme): void => {
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* private mode — ignore */
    }
    setThemeState(next);
  }, []);

  const toggle = useCallback(() => {
    setTheme(readInitial() === "dark" ? "light" : "dark");
  }, [setTheme]);

  return { theme, setTheme, toggle };
}

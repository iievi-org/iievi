"use client";

import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";

import { Button, ButtonLink } from "@/components/linen";
import { registerUpgradeHandler } from "@/lib/ui-events";

interface UpgradeContextValue {
  openUpgrade: (details?: Record<string, unknown>) => void;
  closeUpgrade: () => void;
}

const UpgradeContext = createContext<UpgradeContextValue | null>(null);

export function useUpgradeModal(): UpgradeContextValue {
  const ctx = useContext(UpgradeContext);
  if (!ctx) throw new Error("useUpgradeModal must be used within an UpgradeModalProvider");
  return ctx;
}

/**
 * Renders the upgrade modal and registers the global 402 handler so a
 * plan-limit response anywhere (via the TanStack Query error handler) opens it.
 */
export function UpgradeModalProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [details, setDetails] = useState<Record<string, unknown>>({});

  const openUpgrade = useCallback((next: Record<string, unknown> = {}) => {
    setDetails(next);
    setOpen(true);
  }, []);
  const closeUpgrade = useCallback(() => setOpen(false), []);

  useEffect(() => {
    registerUpgradeHandler((d) => openUpgrade(d));
    return () => registerUpgradeHandler(null);
  }, [openUpgrade]);

  const upgradeTo = typeof details.upgrade_to === "string" ? details.upgrade_to : null;

  return (
    <UpgradeContext.Provider value={{ openUpgrade, closeUpgrade }}>
      {children}
      {open && (
        <div
          role="presentation"
          onClick={closeUpgrade}
          className="fixed inset-0 z-50 flex items-center justify-center p-6"
          style={{ backgroundColor: "rgba(20,17,13,0.55)" }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="upgrade-title"
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md border border-hairline bg-surface p-8"
          >
            <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-signal">
              Plan limit reached
            </p>
            <h2 id="upgrade-title" className="mt-2 font-display text-headline-md text-ink">
              Time to upgrade
            </h2>
            <p className="mt-3 font-body text-body-md text-graphite">
              You&apos;ve hit a limit on your current plan
              {upgradeTo ? `. Upgrade to ${upgradeTo} to keep going.` : "."}
            </p>
            <div className="mt-6 flex gap-3">
              <ButtonLink href="/dashboard/billing" variant="primary" onClick={closeUpgrade}>
                See plans
              </ButtonLink>
              <Button variant="ghost" onClick={closeUpgrade}>
                Not now
              </Button>
            </div>
          </div>
        </div>
      )}
    </UpgradeContext.Provider>
  );
}

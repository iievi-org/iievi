"use client";

import { PLANS, type Plan } from "@iievi/constants";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";

import { Button, ButtonLink } from "@/components/linen";
import {
  formatPlanPrice,
  formatRupees,
  planLabel,
  planPriceRupees,
} from "@/components/billing/plan-format";
import { useCapabilities } from "@/hooks/useCapabilities";
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

function asPlan(value: unknown): Plan | null {
  return typeof value === "string" && (PLANS as readonly string[]).includes(value)
    ? (value as Plan)
    : null;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

/**
 * Renders the upgrade modal and registers the global 402 handler so a
 * plan-limit response anywhere (via the TanStack Query error handler) opens it.
 *
 * The 402 `PlanLimitError.details` payload is `{ current_count, limit,
 * upgrade_to }` (see apps/api/app/core/exceptions.py). We defensively read an
 * optional `message`/`feature`/`resource` too, in case a raiser adds context —
 * but the modal renders correctly from the three guaranteed keys alone.
 */
export function UpgradeModalProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [details, setDetails] = useState<Record<string, unknown>>({});
  const { capabilities } = useCapabilities();
  const dialogRef = useRef<HTMLDivElement>(null);

  const openUpgrade = useCallback((next: Record<string, unknown> = {}) => {
    setDetails(next);
    setOpen(true);
  }, []);
  const closeUpgrade = useCallback(() => setOpen(false), []);

  useEffect(() => {
    registerUpgradeHandler((d) => openUpgrade(d));
    return () => registerUpgradeHandler(null);
  }, [openUpgrade]);

  // Escape to close + move focus into the dialog when it opens.
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent): void => {
      if (e.key === "Escape") closeUpgrade();
    };
    document.addEventListener("keydown", onKeyDown);
    dialogRef.current?.focus();
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, closeUpgrade]);

  // --- Derive the display data from the 402 payload + current capabilities. ---
  const currentPlan = capabilities?.plan ?? null;
  const suggested =
    asPlan(details.upgrade_to) ??
    (currentPlan ? (PLANS[PLANS.indexOf(currentPlan) + 1] ?? null) : null);
  // The backend returns the same plan on the top tier — treat that as "no upgrade".
  const nextPlan = suggested && suggested !== currentPlan ? suggested : null;

  const currentCount = asNumber(details.current_count);
  const currentLimit = asNumber(details.limit);
  const attemptMessage =
    asString(details.message) ?? asString(details.feature) ?? asString(details.resource);

  const priceDelta =
    currentPlan && nextPlan ? planPriceRupees(nextPlan) - planPriceRupees(currentPlan) : null;

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
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="upgrade-title"
            tabIndex={-1}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md border border-hairline bg-surface p-8 focus:outline-none"
          >
            <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-signal">
              Plan limit reached
            </p>
            <h2 id="upgrade-title" className="mt-2 font-display text-headline-md text-ink">
              {nextPlan ? `Upgrade to ${planLabel(nextPlan)}` : "Time to upgrade"}
            </h2>

            <p className="mt-3 font-body text-body-md text-graphite">
              {attemptMessage
                ? `${attemptMessage}. Upgrade to keep going.`
                : "You've hit a limit on your current plan. Upgrade to keep going."}
            </p>

            {/* Usage that tripped the limit, when the payload carries it. */}
            {currentCount != null && currentLimit != null ? (
              <p className="mt-3 font-mono text-mono-sm text-stone tabular-nums">
                Used {currentCount.toLocaleString("en-IN")} of{" "}
                {currentLimit.toLocaleString("en-IN")} on your{" "}
                {currentPlan ? planLabel(currentPlan) : "current"} plan.
              </p>
            ) : null}

            {/* Current plan vs. next plan comparison. */}
            {currentPlan && nextPlan ? (
              <div className="mt-6 border border-hairline">
                <div className="flex divide-x divide-hairline">
                  <div className="flex-1 p-4">
                    <p className="font-mono text-mono-sm uppercase tracking-[0.1em] text-stone">
                      Current
                    </p>
                    <p className="mt-1 font-display text-headline-sm text-ink">
                      {planLabel(currentPlan)}
                    </p>
                    <p className="mt-1 font-mono text-mono-sm text-graphite">
                      {formatPlanPrice(currentPlan)}/mo
                    </p>
                    {currentLimit != null ? (
                      <p className="mt-2 font-mono text-mono-sm text-stone tabular-nums">
                        Limit {currentLimit.toLocaleString("en-IN")}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex-1 bg-neutral p-4">
                    <p className="font-mono text-mono-sm uppercase tracking-[0.1em] text-signal">
                      Recommended
                    </p>
                    <p className="mt-1 font-display text-headline-sm text-ink">
                      {planLabel(nextPlan)}
                    </p>
                    <p className="mt-1 font-mono text-mono-sm text-graphite">
                      {formatPlanPrice(nextPlan)}/mo
                    </p>
                    <p className="mt-2 font-mono text-mono-sm text-ink">
                      {nextPlan === "agency" ? "Unlimited" : "Higher limits"}
                    </p>
                  </div>
                </div>
                {priceDelta != null && priceDelta > 0 ? (
                  <p className="border-t border-hairline px-4 py-3 font-mono text-mono-sm text-stone">
                    +{formatRupees(priceDelta)}/month
                  </p>
                ) : null}
              </div>
            ) : null}

            <div className="mt-6 flex gap-3">
              <ButtonLink
                href="/dashboard/billing"
                variant="primary"
                onClick={closeUpgrade}
                aria-label={nextPlan ? `Upgrade to ${planLabel(nextPlan)}` : "See plans"}
              >
                {nextPlan ? `Upgrade to ${planLabel(nextPlan)}` : "See plans"}
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

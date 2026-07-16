"use client";

/**
 * Billing & plan management.
 *
 * Backend status: only GET /billing/capabilities exists today (surfaced via
 * useCapabilities / usePlanLimits). The following endpoints are still PENDING,
 * so every write path here is a clearly-labelled stub — we never call an
 * endpoint that isn't built:
 *   - POST   /billing/subscribe   (checkout / start a plan)  → PlanCard stub
 *   - POST   /billing/change-plan (upgrade / downgrade)      → PlanCard stub
 *   - GET    /billing/invoices    (invoice history)          → placeholder
 *   - GET    /billing/payment-method                         → placeholder
 * Proration and downgrade-scheduling copy below is ILLUSTRATIVE until the real
 * proration API lands.
 */

import { PLANS, type Plan } from "@iievi/constants";
import { useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { toast } from "sonner";

import { PlanCard } from "@/components/billing/PlanCard";
import {
  formatPlanPrice,
  formatRupees,
  METRIC_LABELS,
  planLabel,
  planPriceRupees,
  USAGE_METRICS,
} from "@/components/billing/plan-format";
import { UsageBar } from "@/components/billing/UsageBar";
import { Rule, SectionLabel } from "@/components/linen";
import { useCapabilities } from "@/hooks/useCapabilities";
import { usePlanLimits } from "@/hooks/usePlanLimits";

/** The plan one tier above `plan`, or null if already on the top plan. */
function nextPlan(plan: Plan): Plan | null {
  const idx = PLANS.indexOf(plan);
  return idx >= 0 && idx < PLANS.length - 1 ? (PLANS[idx + 1] ?? null) : null;
}

/** Runs the "?upgraded=true" success side-effects exactly once on mount. */
function UpgradeSuccessEffect() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const upgraded = searchParams.get("upgraded") === "true";

  useEffect(() => {
    if (!upgraded) return;
    toast.success("You're upgraded!");
    void queryClient.invalidateQueries({ queryKey: ["capabilities"] });
  }, [upgraded, queryClient]);

  return null;
}

function CurrentPlanCard() {
  const { capabilities, isSuspended } = useCapabilities();
  const plan = capabilities?.plan ?? null;

  return (
    <div className="border border-hairline bg-neutral p-8">
      <SectionLabel>Current plan</SectionLabel>
      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-4">
        <h2 className="font-display text-headline-lg text-ink">
          {plan ? planLabel(plan) : "…"}
        </h2>
        {plan ? (
          <p className="font-mono text-mono-sm text-stone">
            <span className="text-stat-numeral font-display text-ink">
              {formatPlanPrice(plan)}
            </span>
            <span className="ml-1.5">/ month</span>
          </p>
        ) : null}
      </div>

      {isSuspended ? (
        <div className="mt-6 border border-signal bg-surface p-4" role="alert">
          <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-signal">
            Account suspended
          </p>
          <p className="mt-1 font-body text-body-sm text-graphite">
            Your account is suspended and most actions are paused. Settle any outstanding balance or
            contact support to restore access.
          </p>
        </div>
      ) : null}
    </div>
  );
}

function UsageSection() {
  const { usage, limits, isAtLimit } = usePlanLimits();

  return (
    <section className="border border-hairline bg-surface p-8">
      <div className="flex items-baseline justify-between gap-4">
        <SectionLabel>This month&apos;s usage</SectionLabel>
        <span className="font-mono text-mono-sm text-stone">Resets monthly</span>
      </div>

      {usage && limits ? (
        <div className="mt-6 space-y-5">
          {USAGE_METRICS.map((metric) => (
            <UsageBar
              key={metric}
              label={METRIC_LABELS[metric]}
              used={usage[metric]}
              limit={limits[metric]}
              atLimit={isAtLimit(metric)}
            />
          ))}
        </div>
      ) : (
        <p className="mt-6 font-body text-body-sm text-stone">Loading usage…</p>
      )}
    </section>
  );
}

/** Illustrative proration / scheduling copy shown near the plan actions. */
function ProrationNote({ currentPlan }: { currentPlan: Plan }) {
  const upgradeTo = nextPlan(currentPlan);
  // A rough, illustrative half-period proration figure — NOT a real quote.
  const proratedRupees =
    upgradeTo != null
      ? Math.round((planPriceRupees(upgradeTo) - planPriceRupees(currentPlan)) / 2)
      : 0;
  const nextChangeDate = new Date();
  nextChangeDate.setMonth(nextChangeDate.getMonth() + 1);
  const changeDateLabel = nextChangeDate.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "long",
  });

  return (
    <div className="border border-hairline bg-neutral p-6">
      <SectionLabel>How plan changes work</SectionLabel>
      <ul className="mt-4 space-y-3 font-body text-body-sm text-graphite">
        <li className="flex gap-3">
          <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-ink" />
          <span>
            <span className="text-ink">Upgrades apply instantly.</span>{" "}
            {upgradeTo != null ? (
              <>
                You&apos;ll be charged about {formatRupees(Math.max(proratedRupees, 0))} today for the
                remainder of this billing period, then {formatPlanPrice(upgradeTo)}/month going
                forward.
              </>
            ) : (
              <>You&apos;re on the top plan — nothing higher to move to.</>
            )}
          </span>
        </li>
        <li className="flex gap-3">
          <span aria-hidden="true" className="mt-2 h-1 w-1 shrink-0 rounded-full bg-ink" />
          <span>
            <span className="text-ink">Downgrades are scheduled.</span> Your plan changes on{" "}
            {changeDateLabel}, at the end of your current billing period — you keep your current
            limits until then.
          </span>
        </li>
      </ul>
      <p className="mt-4 font-mono text-mono-sm text-stone">
        Figures are illustrative — exact proration is calculated at checkout once billing is live.
      </p>
    </div>
  );
}

function PlanComparison() {
  const { capabilities } = useCapabilities();
  const currentPlan = capabilities?.plan ?? PLANS[0];

  return (
    <section>
      <SectionLabel>Plans</SectionLabel>
      <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {PLANS.map((plan) => (
          <PlanCard key={plan} plan={plan} currentPlan={currentPlan} />
        ))}
      </div>
      <div className="mt-6">
        <ProrationNote currentPlan={currentPlan} />
      </div>
    </section>
  );
}

/** Placeholder for payment method + invoice history (no backend yet). */
function BillingPlaceholders() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <section className="border border-hairline bg-surface p-8">
        <SectionLabel>Payment method</SectionLabel>
        <p className="mt-4 font-display text-headline-sm text-ink">No card on file</p>
        <p className="mt-2 font-body text-body-sm text-stone">
          Adding a payment method and managing cards arrives with checkout — coming soon.
        </p>
      </section>

      <section className="border border-hairline bg-surface p-8">
        <SectionLabel>Invoice history</SectionLabel>
        <p className="mt-4 font-display text-headline-sm text-ink">No invoices yet</p>
        <p className="mt-2 font-body text-body-sm text-stone">
          Downloadable invoices and receipts will appear here once billing is live — coming soon.
        </p>
      </section>
    </div>
  );
}

function BillingContent() {
  return (
    <div className="mx-auto max-w-[1100px] p-6 md:p-10">
      <header>
        <SectionLabel>Billing</SectionLabel>
        <h1 className="mt-2 font-display text-headline-md text-ink">Plan &amp; billing</h1>
        <p className="mt-2 max-w-2xl font-body text-body-md text-graphite">
          Track your monthly usage, compare plans and manage your subscription.
        </p>
      </header>

      <Rule className="my-8" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <CurrentPlanCard />
        <UsageSection />
      </div>

      <div className="mt-10">
        <PlanComparison />
      </div>

      <Rule className="my-10" />

      <BillingPlaceholders />
    </div>
  );
}

export default function BillingPage() {
  return (
    <>
      {/* useSearchParams must sit under a Suspense boundary (Next App Router). */}
      <Suspense fallback={null}>
        <UpgradeSuccessEffect />
      </Suspense>
      <BillingContent />
    </>
  );
}

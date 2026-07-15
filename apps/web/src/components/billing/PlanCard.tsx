"use client";

/**
 * One plan in the comparison grid. Shows the monthly price, the per-metric
 * quotas from PLAN_LIMITS, and a single action:
 *   - the current plan is marked (ink border + "Current plan" badge), no action
 *   - higher plans get an "Upgrade" button, lower plans a "Downgrade" button
 *
 * NOTE: `POST /billing/subscribe` (checkout) does not exist yet, so the action
 * is a deliberate stub — it toasts "coming soon" and calls nothing. See the
 * page-level comment for the full list of pending billing endpoints.
 */

import { PLAN_LIMITS, PLANS, type Plan } from "@iievi/constants";
import { toast } from "sonner";

import { Button } from "@/components/linen";

import {
  formatPlanPrice,
  METRIC_LABELS,
  planLabel,
  PLAN_TAGLINES,
  USAGE_METRICS,
} from "./plan-format";

type Direction = "current" | "upgrade" | "downgrade";

function directionFor(plan: Plan, current: Plan): Direction {
  if (plan === current) return "current";
  return PLANS.indexOf(plan) > PLANS.indexOf(current) ? "upgrade" : "downgrade";
}

export function PlanCard({ plan, currentPlan }: { plan: Plan; currentPlan: Plan }) {
  const direction = directionFor(plan, currentPlan);
  const isCurrent = direction === "current";
  const limits = PLAN_LIMITS[plan];

  const handleAction = (): void => {
    // Checkout / plan-change endpoint is not built yet — keep this honest.
    toast("Checkout is being wired up — coming soon");
  };

  return (
    <div
      className={`flex flex-col border p-6 ${
        isCurrent ? "border-ink bg-neutral" : "border-hairline bg-surface"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-display text-headline-sm text-ink">{planLabel(plan)}</h3>
        {isCurrent ? (
          <span className="border border-ink px-2 py-0.5 font-mono text-mono-sm uppercase tracking-[0.1em] text-ink">
            Current
          </span>
        ) : null}
      </div>

      <p className="mt-1 min-h-[2.4em] font-body text-body-sm text-stone">{PLAN_TAGLINES[plan]}</p>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="font-display text-headline-md text-ink">{formatPlanPrice(plan)}</span>
        <span className="font-mono text-mono-sm text-stone">/mo</span>
      </div>

      <dl className="mt-5 flex-1 space-y-2 border-t border-hairline pt-5">
        {USAGE_METRICS.map((metric) => {
          const limit = limits[metric];
          return (
            <div key={metric} className="flex items-baseline justify-between gap-3">
              <dt className="font-body text-body-sm text-graphite">{METRIC_LABELS[metric]}</dt>
              <dd className="font-mono text-mono-sm text-ink tabular-nums">
                {limit === null ? "Unlimited" : limit.toLocaleString("en-IN")}
              </dd>
            </div>
          );
        })}
      </dl>

      <div className="mt-6">
        {isCurrent ? (
          <Button variant="ghost" disabled className="w-full">
            Current plan
          </Button>
        ) : (
          <Button
            variant={direction === "upgrade" ? "primary" : "ghost"}
            onClick={handleAction}
            className="w-full"
          >
            {direction === "upgrade" ? "Upgrade" : "Downgrade"}
          </Button>
        )}
      </div>
    </div>
  );
}

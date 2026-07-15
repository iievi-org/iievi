"use client";

import { Card } from "@/components/linen";
import { useCapabilities } from "@/hooks/useCapabilities";
import { usePlanLimits } from "@/hooks/usePlanLimits";

export default function BillingPage() {
  const { capabilities } = useCapabilities();
  const { usage } = usePlanLimits();
  return (
    <div className="p-8">
      <h1 className="font-display text-headline-md text-ink">Billing</h1>
      <Card variant="paper" className="mt-6 max-w-md">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">Current plan</p>
        <p className="mt-1 font-display text-headline-sm text-ink capitalize">
          {capabilities?.plan ?? "…"}
        </p>
        {usage ? (
          <p className="mt-4 font-body text-body-sm text-graphite">
            {usage.posts_generated} posts · {usage.leads_captured} leads captured this month
          </p>
        ) : null}
      </Card>
      <p className="mt-4 font-body text-body-sm text-stone">
        Plan management lands in a later phase.
      </p>
    </div>
  );
}

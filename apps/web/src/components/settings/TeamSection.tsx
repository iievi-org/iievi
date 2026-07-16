"use client";

import { Users } from "lucide-react";

import { ComingSoon } from "@/components/dashboard/ComingSoon";
import { ButtonLink, Card } from "@/components/linen";
import { useCapabilities } from "@/hooks/useCapabilities";

export function TeamSection() {
  const { capabilities, query } = useCapabilities();

  if (query.isLoading) {
    return (
      <p className="font-body text-body-sm text-stone" role="status">
        Loading…
      </p>
    );
  }

  // Team management is an Agency-plan feature. Anyone below Agency gets an
  // upgrade prompt instead of the (not-yet-built) team UI.
  if (capabilities?.plan !== "agency") {
    return (
      <Card variant="paper" className="max-w-2xl">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-signal">
          Agency plan
        </p>
        <h3 className="mt-3 font-display text-headline-md text-ink">Team management</h3>
        <p className="mt-3 max-w-prose font-body text-body-md text-graphite">
          Invite teammates, assign roles, and collaborate on leads and posts. Team management is
          available on the Agency plan.
        </p>
        <div className="mt-6">
          <ButtonLink href="/dashboard/billing">Upgrade to Agency</ButtonLink>
        </div>
      </Card>
    );
  }

  // Agency plan, but no team backend exists yet.
  return (
    <ComingSoon
      icon={Users}
      eyebrow="Agency"
      title="Team management is coming"
      description="You're on the Agency plan. Inviting teammates and managing their access will land here soon."
      bullets={[
        "Invite members by email",
        "Assign owner, admin, or member roles",
        "Shared access to leads, posts, and analytics",
      ]}
      note="No action needed right now"
    />
  );
}

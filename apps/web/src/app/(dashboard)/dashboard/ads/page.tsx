"use client";

import { Megaphone } from "lucide-react";

import { ComingSoon } from "@/components/dashboard/ComingSoon";
import { ButtonLink } from "@/components/linen";
import { useCapabilities } from "@/hooks/useCapabilities";

export default function AdsPage() {
  const { hasFeature } = useCapabilities();

  if (!hasFeature("can_create_ads")) {
    return (
      <ComingSoon
        icon={Megaphone}
        eyebrow="Ads · Growth & Agency"
        title="Ad campaigns"
        description="Launch and manage Meta ad campaigns without leaving your dashboard. This is available on the Growth and Agency plans."
        note="Upgrade to unlock ads."
      >
        <ButtonLink href="/dashboard/billing" variant="ghost">
          View plans
        </ButtonLink>
      </ComingSoon>
    );
  }

  return (
    <ComingSoon
      icon={Megaphone}
      eyebrow="Ads"
      title="Campaign management is coming"
      description="Soon you'll launch and monitor your Meta campaigns right here — from a single brief to live performance."
      bullets={[
        "Objective, budget & targeting",
        "Live spend, leads and CPL",
        "Pause / resume in one click",
      ]}
      note="Ads backend in progress."
    />
  );
}

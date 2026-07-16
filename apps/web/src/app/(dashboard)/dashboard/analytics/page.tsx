import { BarChart3 } from "lucide-react";

import { ComingSoon } from "@/components/dashboard/ComingSoon";
import { ButtonLink } from "@/components/linen";

export default function AnalyticsPage() {
  return (
    <ComingSoon
      icon={BarChart3}
      eyebrow="Analytics"
      title="Analytics dashboards"
      description="KPI trends, lead-source breakdowns, conversion funnels and top-post tables are being wired up."
      bullets={[
        "Leads, reach, spend & CPL KPIs",
        "Conversion funnel with drop-off",
        "Top posts, sortable",
      ]}
      note="Analytics data API in progress."
    >
      <ButtonLink href="/dashboard/leads" variant="ghost">
        See your leads
      </ButtonLink>
    </ComingSoon>
  );
}

import type { Lead } from "@iievi/types";

import { Badge } from "@/components/linen";
import { LEAD_STATUS_META, PLATFORM_META } from "@/lib/status";
import { relativeTime } from "@/lib/time";

export function LeadCard({
  lead,
  active,
  onSelect,
}: {
  lead: Lead;
  active: boolean;
  onSelect: () => void;
}) {
  const status = LEAD_STATUS_META[lead.status];
  const platform = PLATFORM_META[lead.platform];
  const preview =
    typeof lead.metadata?.["preview"] === "string"
      ? (lead.metadata["preview"] as string)
      : `via ${platform?.label ?? lead.source}`;
  const when = lead.last_inbound_at ?? lead.updated_at;

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-current={active ? "true" : undefined}
      className={`block w-full border-b border-hairline px-4 py-3 text-left transition-colors ${
        active ? "bg-neutral" : "hover:bg-neutral"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span
            aria-hidden="true"
            className="inline-flex h-6 w-6 shrink-0 items-center justify-center border border-hairline font-mono text-[10px] text-graphite"
          >
            {platform?.short ?? "?"}
          </span>
          <span className="truncate font-body text-body-md text-ink">{lead.name ?? "Unknown"}</span>
        </div>
        <span className="shrink-0 font-mono text-mono-sm text-stone">{relativeTime(when)}</span>
      </div>
      <div className="mt-1.5 flex items-center justify-between gap-2">
        <span className="truncate font-body text-body-sm text-graphite">{preview}</span>
        <Badge color={status?.color} className="shrink-0">
          {status?.label ?? lead.status}
        </Badge>
      </div>
    </button>
  );
}

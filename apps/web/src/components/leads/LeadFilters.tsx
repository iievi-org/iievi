"use client";

import type { LeadStatus, Platform } from "@iievi/types";
import { X } from "lucide-react";

import { LEAD_STATUS_META, PLATFORM_META } from "@/lib/status";

const STATUSES: LeadStatus[] = ["new", "engaged", "qualified", "booked", "won", "lost"];
const PLATFORMS: Platform[] = ["meta", "instagram", "whatsapp", "tiktok", "linkedin"];

interface LeadFiltersProps {
  statuses: Set<LeadStatus>;
  platforms: Set<Platform>;
  from: string;
  to: string;
  onToggleStatus: (status: LeadStatus) => void;
  onTogglePlatform: (platform: Platform) => void;
  onDateChange: (which: "from" | "to", value: string) => void;
  onClear: () => void;
}

export function LeadFilters({
  statuses,
  platforms,
  from,
  to,
  onToggleStatus,
  onTogglePlatform,
  onDateChange,
  onClear,
}: LeadFiltersProps) {
  const anyActive = statuses.size > 0 || platforms.size > 0 || from !== "" || to !== "";

  return (
    <div className="flex flex-col gap-3 border-b border-hairline p-4">
      {/* Status chips */}
      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by status">
        {STATUSES.map((status) => {
          const meta = LEAD_STATUS_META[status];
          const on = statuses.has(status);
          return (
            <button
              key={status}
              type="button"
              aria-pressed={on}
              onClick={() => onToggleStatus(status)}
              className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-body text-label-sm uppercase tracking-[0.1em] transition-colors ${
                on ? "border-ink bg-ink text-surface" : "border-hairline text-graphite hover:text-ink"
              }`}
            >
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: meta.color }}
              />
              {meta.label}
            </button>
          );
        })}
      </div>

      {/* Platform toggles + date range + clear */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by platform">
          {PLATFORMS.map((platform) => {
            const on = platforms.has(platform);
            return (
              <button
                key={platform}
                type="button"
                aria-pressed={on}
                aria-label={PLATFORM_META[platform].label}
                onClick={() => onTogglePlatform(platform)}
                className={`inline-flex h-8 min-w-8 items-center justify-center border px-2 font-mono text-mono-sm transition-colors ${
                  on ? "border-ink bg-ink text-surface" : "border-hairline text-graphite hover:text-ink"
                }`}
              >
                {PLATFORM_META[platform].short}
              </button>
            );
          })}
        </div>

        <label className="flex flex-col gap-1">
          <span className="font-mono text-mono-sm uppercase tracking-[0.1em] text-stone">From</span>
          <input
            type="date"
            value={from}
            onChange={(e) => onDateChange("from", e.target.value)}
            className="border-0 border-b border-t border-hairline bg-transparent px-0 py-1.5 font-body text-body-sm text-ink outline-none focus:border-b-signal"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="font-mono text-mono-sm uppercase tracking-[0.1em] text-stone">To</span>
          <input
            type="date"
            value={to}
            onChange={(e) => onDateChange("to", e.target.value)}
            className="border-0 border-b border-t border-hairline bg-transparent px-0 py-1.5 font-body text-body-sm text-ink outline-none focus:border-b-signal"
          />
        </label>

        {anyActive ? (
          <button
            type="button"
            onClick={onClear}
            className="inline-flex items-center gap-1 py-1.5 font-body text-body-sm text-graphite transition-colors hover:text-signal"
          >
            <X size={14} aria-hidden="true" />
            Clear
          </button>
        ) : null}
      </div>
    </div>
  );
}

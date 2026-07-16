import type { LeadStatus, Platform } from "@iievi/types";

/**
 * Status/platform display metadata shared across the dashboard. Colours are a
 * restrained, semantic extension of the Linen palette — used ONLY for status
 * coding (badges, dots), never as decoration.
 */

export type StatusGroup = "new" | "progressing" | "decision" | "resolved" | "terminal";

interface StatusMeta {
  label: string;
  group: StatusGroup;
  /** Foreground colour for text/dot. */
  color: string;
}

/** Semantic status colours (hex — Linen tokens are CSS vars, so status uses literals). */
export const STATUS_COLORS: Record<StatusGroup, string> = {
  new: "#2f6f9f", // blue — fresh
  progressing: "#c8462c", // signal accent — being worked
  decision: "#b8791f", // amber — needs a decision
  resolved: "#3f8f5b", // green — won/booked
  terminal: "#8a857c", // stone — closed/lost
};

export const LEAD_STATUS_META: Record<LeadStatus, StatusMeta> = {
  new: { label: "New", group: "new", color: STATUS_COLORS.new },
  engaged: { label: "Engaged", group: "progressing", color: STATUS_COLORS.progressing },
  qualified: { label: "Qualified", group: "decision", color: STATUS_COLORS.decision },
  booked: { label: "Booked", group: "resolved", color: STATUS_COLORS.resolved },
  won: { label: "Won", group: "resolved", color: STATUS_COLORS.resolved },
  lost: { label: "Lost", group: "terminal", color: STATUS_COLORS.terminal },
};

/** Valid next statuses, mirroring the backend transition table. */
export const LEAD_STATUS_TRANSITIONS: Record<LeadStatus, LeadStatus[]> = {
  new: ["engaged", "qualified", "lost"],
  engaged: ["qualified", "booked", "lost"],
  qualified: ["booked", "won", "lost"],
  booked: ["won", "lost"],
  won: [],
  lost: ["new"],
};

export const PLATFORM_META: Record<Platform, { label: string; short: string }> = {
  meta: { label: "Meta", short: "M" },
  instagram: { label: "Instagram", short: "IG" },
  whatsapp: { label: "WhatsApp", short: "WA" },
  tiktok: { label: "TikTok", short: "TT" },
  linkedin: { label: "LinkedIn", short: "in" },
};

export const PLAN_LABELS: Record<string, string> = {
  trial: "Trial",
  starter: "Starter",
  growth: "Growth",
  agency: "Agency",
};

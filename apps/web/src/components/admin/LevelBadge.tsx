import { Badge } from "@/components/linen";

/**
 * Log-level → status-dot colour, per the Linen palette. Unknown/absent levels
 * fall back to the muted stone dot with an "UNKNOWN" label.
 */
const LEVEL_COLORS: Record<string, string> = {
  CRITICAL: "#b4402f",
  ERROR: "#b4402f",
  WARNING: "#b8791f",
  INFO: "#2f6f9f",
  DEBUG: "#8a857c",
};

export function LevelBadge({ level }: { level?: string | undefined }) {
  const upper = (level ?? "").toUpperCase();
  const color = LEVEL_COLORS[upper] ?? "#8a857c";
  return <Badge color={color}>{upper || "UNKNOWN"}</Badge>;
}

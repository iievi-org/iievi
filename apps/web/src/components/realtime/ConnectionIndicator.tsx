"use client";

import { useWebSocket } from "@/lib/websocket";

/** The Live (green) / Reconnecting (amber) dot for the dashboard sidebar. */
export function ConnectionIndicator({ className = "" }: { className?: string }) {
  const { status } = useWebSocket();
  const connected = status === "connected";
  return (
    <span
      className={`inline-flex items-center gap-2 font-mono text-mono-sm uppercase tracking-[0.14em] text-stone ${className}`}
    >
      <span
        aria-hidden="true"
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: connected ? "#3f8f5b" : "var(--focus)" }}
      />
      {connected ? "Live" : "Reconnecting"}
    </span>
  );
}

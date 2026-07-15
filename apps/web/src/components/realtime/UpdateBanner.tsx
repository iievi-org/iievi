"use client";

import { useWebSocket } from "@/lib/websocket";

/** "New update available" banner, raised by a deployment_notification event. */
export function UpdateBanner() {
  const { updateAvailable, dismissUpdate } = useWebSocket();
  if (!updateAvailable) return null;
  return (
    <div
      role="status"
      className="sticky top-0 z-40 flex items-center justify-center gap-4 border-b border-hairline bg-ink px-4 py-2 text-surface"
    >
      <span className="font-mono text-mono-sm uppercase tracking-[0.14em]">
        New update available
      </span>
      <button
        type="button"
        onClick={() => typeof window !== "undefined" && window.location.reload()}
        className="font-mono text-mono-sm uppercase tracking-[0.14em] underline"
      >
        Click to refresh
      </button>
      <button
        type="button"
        aria-label="Dismiss update notification"
        onClick={dismissUpdate}
        className="ml-2 font-mono text-body-sm"
      >
        ×
      </button>
    </div>
  );
}

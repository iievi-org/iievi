"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useWebSocket } from "@/lib/websocket";

/**
 * Client-side unread-leads counter for the nav badge. Increments on each
 * `new_lead` WebSocket event and resets to zero whenever the user is on the
 * leads inbox (they've "seen" them).
 */
export function useUnreadLeads(): number {
  const { subscribe } = useWebSocket();
  const pathname = usePathname();
  const [count, setCount] = useState(0);

  useEffect(() => subscribe("new_lead", () => setCount((c) => c + 1)), [subscribe]);

  useEffect(() => {
    if (pathname.startsWith("/dashboard/leads")) setCount(0);
  }, [pathname]);

  return count;
}

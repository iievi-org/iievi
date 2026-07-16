"use client";

/**
 * Realtime WebSocket client (Prompt 8 Step 9).
 *
 * Fetches a one-time ws-token, connects to /ws/{tenant_id}?token=…, and
 * reconnects with exponential backoff (1s → 2s → 4s → 8s → … → 30s). Events are
 * delivered through a typed publish/subscribe API (useWebSocket().subscribe) and
 * a few are handled centrally: new_lead invalidates the leads query and toasts;
 * notification_count_changed invalidates notifications; deployment_notification
 * raises the "update available" banner. The connection status drives the
 * Live/Reconnecting dot in the sidebar.
 */

import type { JsonObject, WsMessage } from "@iievi/types";
import { useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { toast } from "sonner";

import { API_BASE_URL, api } from "./api";
import { useAuth } from "./auth-context";

export type ConnectionStatus = "connecting" | "connected" | "disconnected";
type EventHandler = (data: JsonObject) => void;

interface WebSocketContextValue {
  status: ConnectionStatus;
  /** Subscribe to an event type; returns an unsubscribe function. */
  subscribe: (type: string, handler: EventHandler) => () => void;
  updateAvailable: boolean;
  dismissUpdate: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function useWebSocket(): WebSocketContextValue {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error("useWebSocket must be used within a WebSocketProvider");
  return ctx;
}

const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");
const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30_000;

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const [updateAvailable, setUpdateAvailable] = useState(false);

  const handlers = useRef<Map<string, Set<EventHandler>>>(new Map());

  const subscribe = useCallback((type: string, handler: EventHandler): (() => void) => {
    const set = handlers.current.get(type) ?? new Set<EventHandler>();
    set.add(handler);
    handlers.current.set(type, set);
    return () => {
      set.delete(handler);
    };
  }, []);

  const tenantId = user?.tenantId;

  useEffect(() => {
    if (!tenantId) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let backoff = INITIAL_BACKOFF_MS;
    let disposed = false;

    const scheduleReconnect = (): void => {
      if (disposed) return;
      const delay = backoff;
      backoff = Math.min(backoff * 2, MAX_BACKOFF_MS);
      reconnectTimer = setTimeout(() => void connect(), delay);
    };

    const handleCentral = (message: WsMessage): void => {
      switch (message.type) {
        case "new_lead": {
          void queryClient.invalidateQueries({ queryKey: ["leads"] });
          const name = typeof message.data.name === "string" ? message.data.name : null;
          toast(name ? `New lead: ${name}` : "New lead received");
          break;
        }
        case "lead_status_changed":
        case "new_message":
        case "lead_handed_off":
          void queryClient.invalidateQueries({ queryKey: ["leads"] });
          break;
        case "notification_count_changed":
          void queryClient.invalidateQueries({ queryKey: ["notifications"] });
          break;
        case "deployment_notification":
          setUpdateAvailable(true);
          break;
        default:
          break;
      }
    };

    const connect = async (): Promise<void> => {
      if (disposed) return;
      setStatus("connecting");
      let token: string;
      try {
        token = (await api.auth.wsToken()).token;
      } catch {
        scheduleReconnect();
        return;
      }
      if (disposed) return;
      const ws = new WebSocket(`${WS_BASE_URL}/ws/${tenantId}?token=${encodeURIComponent(token)}`);
      socket = ws;
      ws.onopen = () => {
        backoff = INITIAL_BACKOFF_MS;
        setStatus("connected");
      };
      ws.onmessage = (event: MessageEvent<string>) => {
        try {
          const message = JSON.parse(event.data) as WsMessage;
          handleCentral(message);
          handlers.current.get(message.type)?.forEach((h) => h(message.data));
        } catch {
          /* ignore malformed frames */
        }
      };
      ws.onclose = () => {
        setStatus("disconnected");
        scheduleReconnect();
      };
      ws.onerror = () => ws.close();
    };

    void connect();

    return () => {
      disposed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [tenantId, queryClient]);

  return (
    <WebSocketContext.Provider
      value={{ status, subscribe, updateAvailable, dismissUpdate: () => setUpdateAvailable(false) }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

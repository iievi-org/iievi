"use client";

import type { ConversationMessage, JsonObject } from "@iievi/types";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { ConversationSkeleton } from "@/components/skeletons/Skeletons";
import { api } from "@/lib/api";
import { clockTime } from "@/lib/time";
import { useWebSocket } from "@/lib/websocket";

import { TakeoverBar } from "./TakeoverBar";

function MessageBubble({ message }: { message: ConversationMessage }) {
  if (message.role === "system") {
    return (
      <li className="flex justify-center">
        <span className="border border-hairline bg-neutral px-3 py-1 text-center font-mono text-mono-sm text-stone">
          {message.content}
        </span>
      </li>
    );
  }
  const isCustomer = message.role === "lead";
  const isHuman = message.role === "human_agent";
  const onLight = isCustomer || isHuman;
  return (
    <li className={`flex ${isCustomer ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[80%] px-3 py-2 ${
          isCustomer
            ? "border border-hairline bg-neutral text-ink"
            : isHuman
              ? "border border-ink bg-surface text-ink"
              : "bg-ink text-surface"
        }`}
      >
        <p className="whitespace-pre-wrap font-body text-body-sm">{message.content}</p>
        <span
          className={`mt-1 block font-mono text-[10px] ${onLight ? "text-stone" : "text-surface opacity-70"}`}
        >
          {clockTime(message.created_at)}
          {isHuman ? " · you" : ""}
        </span>
      </div>
    </li>
  );
}

function TypingIndicator() {
  return (
    <li className="flex justify-end" aria-label="AI is typing">
      <div className="flex items-center gap-1 bg-ink px-3 py-3">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-surface"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </li>
  );
}

/** The full thread for one lead: live messages, typing indicator, takeover bar. */
export function ConversationPanel({ leadId }: { leadId: string }) {
  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const leadQuery = useQuery({ queryKey: ["lead", leadId], queryFn: () => api.leads.get(leadId) });
  const convQuery = useQuery({
    queryKey: ["conversation", leadId],
    queryFn: () => api.leads.conversation(leadId),
    staleTime: 30_000,
  });

  useEffect(() => {
    const isThisLead = (data: JsonObject) => data["lead_id"] === leadId;
    const invalidateConversation = () =>
      void queryClient.invalidateQueries({ queryKey: ["conversation", leadId] });
    const unsubs = [
      subscribe("ai_typing_started", (d) => {
        if (isThisLead(d)) setTyping(true);
      }),
      subscribe("ai_response_sent", (d) => {
        if (isThisLead(d)) {
          setTyping(false);
          invalidateConversation();
          void queryClient.invalidateQueries({ queryKey: ["lead", leadId] });
        }
      }),
      subscribe("new_message", (d) => {
        if (isThisLead(d)) invalidateConversation();
      }),
    ];
    return () => unsubs.forEach((u) => u());
  }, [subscribe, leadId, queryClient]);

  const messages = convQuery.data?.messages ?? [];

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight });
  }, [messages.length, typing]);

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto p-4">
        {convQuery.isLoading ? (
          <ConversationSkeleton />
        ) : messages.length === 0 ? (
          <p className="py-16 text-center font-body text-body-sm text-stone">No messages yet.</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {typing ? <TypingIndicator /> : null}
          </ul>
        )}
      </div>
      {leadQuery.data ? <TakeoverBar lead={leadQuery.data} /> : null}
    </div>
  );
}

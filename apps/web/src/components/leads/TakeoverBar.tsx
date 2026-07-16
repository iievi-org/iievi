"use client";

import type { Lead } from "@iievi/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { Send } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { LINEN_EASE } from "@/lib/animations";

/** Transitions between the "AI is handling" indicator and a manual reply box. */
export function TakeoverBar({ lead }: { lead: Lead }) {
  const queryClient = useQueryClient();
  const [text, setText] = useState("");

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["lead", lead.id] });
    void queryClient.invalidateQueries({ queryKey: ["conversation", lead.id] });
    void queryClient.invalidateQueries({ queryKey: ["leads"] });
  };

  const takeOver = useMutation({
    mutationFn: () => api.leads.takeOver(lead.id),
    onSuccess: invalidate,
    onError: () => toast.error("Couldn't take over this conversation"),
  });
  const resumeAi = useMutation({
    mutationFn: () => api.leads.resumeAi(lead.id),
    onSuccess: invalidate,
    onError: () => toast.error("Couldn't hand back to the AI"),
  });
  const send = useMutation({
    mutationFn: (value: string) => api.leads.sendMessage(lead.id, value),
    onSuccess: () => {
      setText("");
      invalidate();
    },
    onError: () => toast.error("Message failed to send"),
  });

  const submit = () => {
    const value = text.trim();
    if (value) send.mutate(value);
  };

  return (
    <div className="border-t border-hairline bg-surface p-3">
      <AnimatePresence mode="wait" initial={false}>
        {lead.manual_mode ? (
          <motion.div
            key="manual"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: LINEN_EASE }}
            className="flex items-end gap-2"
          >
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
              rows={1}
              placeholder="Type a reply…"
              aria-label="Manual reply"
              className="min-h-[42px] flex-1 resize-none border border-hairline bg-surface px-3 py-2 font-body text-body-sm text-ink outline-none transition-colors focus:border-signal"
            />
            <button
              type="button"
              onClick={submit}
              disabled={send.isPending || text.trim() === ""}
              aria-label="Send reply"
              className="inline-flex h-[42px] w-[42px] items-center justify-center border border-ink bg-ink text-surface transition-colors hover:bg-surface hover:text-ink disabled:opacity-40"
            >
              <Send size={16} strokeWidth={1.75} aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={() => resumeAi.mutate()}
              disabled={resumeAi.isPending}
              className="h-[42px] whitespace-nowrap border border-hairline px-3 font-body text-label-sm uppercase tracking-[0.1em] text-graphite transition-colors hover:text-ink disabled:opacity-40"
            >
              Resume AI
            </button>
          </motion.div>
        ) : (
          <motion.div
            key="ai"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2, ease: LINEN_EASE }}
            className="flex items-center justify-between gap-3 px-1 py-2"
          >
            <span className="flex items-center gap-2 font-body text-body-sm text-graphite">
              <span className="relative flex h-2 w-2" aria-hidden="true">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#3f8f5b] opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#3f8f5b]" />
              </span>
              AI is handling this conversation
            </span>
            <button
              type="button"
              onClick={() => takeOver.mutate()}
              disabled={takeOver.isPending}
              className="whitespace-nowrap border border-ink px-3 py-1.5 font-body text-label-sm uppercase tracking-[0.1em] text-ink transition-colors hover:bg-ink hover:text-surface disabled:opacity-40"
            >
              Take over
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";

export interface ChatMessage {
  from: "user" | "ai";
  text: string;
  time?: string;
}

interface ChatMockupProps {
  title?: string;
  messages: ChatMessage[];
  className?: string;
}

export function ChatMockup({
  title = "WhatsApp Business",
  messages,
  className = "",
}: ChatMockupProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });
  const reduce = useReducedMotion();
  const [shown, setShown] = useState(reduce ? messages.length : 0);

  useEffect(() => {
    if (!inView || reduce) return;
    if (shown >= messages.length) return;
    const t = setTimeout(() => setShown(shown + 1), 700);
    return () => clearTimeout(t);
  }, [inView, shown, messages.length, reduce]);

  return (
    <div ref={ref} className={`bg-neutral border border-hairline ${className}`}>
      <div className="flex items-center justify-between px-5 py-3 border-b border-hairline">
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">{title}</p>
        <span className="inline-block w-2 h-2 rounded-full bg-signal" />
      </div>
      <div className="p-5 flex flex-col gap-3 min-h-[320px]">
        {messages.slice(0, shown).map((m, i) => {
          const mine = m.from === "user";
          return (
            <div key={i} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
              <div className="max-w-[78%] flex flex-col gap-1">
                <div
                  className={`px-4 py-2.5 text-body-sm ${
                    mine ? "bg-ink text-surface" : "bg-transparent border border-hairline text-ink"
                  }`}
                >
                  {m.text}
                </div>
                {m.time && (
                  <span className={`font-mono text-mono-sm text-stone ${mine ? "text-right" : ""}`}>
                    {mine ? "You" : "IIEVI AI"} · {m.time}
                  </span>
                )}
              </div>
            </div>
          );
        })}
        {!reduce && shown < messages.length && (
          <div className="flex justify-start">
            <div className="px-4 py-3 border border-hairline flex gap-1">
              <span className="w-1.5 h-1.5 bg-stone rounded-full animate-pulse" />
              <span className="w-1.5 h-1.5 bg-stone rounded-full animate-pulse [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 bg-stone rounded-full animate-pulse [animation-delay:300ms]" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

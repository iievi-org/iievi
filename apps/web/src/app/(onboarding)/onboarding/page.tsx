"use client";

import { Send } from "lucide-react";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useReducer, useRef, useState } from "react";

import { Button, ButtonLink } from "@/components/linen";
import { CategoryGrid } from "@/components/onboarding/CategoryGrid";
import { Confetti } from "@/components/onboarding/Confetti";
import {
  initialOnboardingState,
  onboardingReducer,
  typingDelayMs,
} from "@/components/onboarding/reducer";
import { TypingDots } from "@/components/onboarding/TypingDots";
import { api } from "@/lib/api";
import { mark, measureRoundtrip } from "@/lib/perf";

const STAGE_ORDER = [
  "welcome",
  "category_select",
  "business_info",
  "business_overview",
  "target_audience",
  "existing_customers",
  "competitor_analysis",
  "brand_identity",
  "creative_preferences",
  "marketing_goals",
  "lead_management",
  "confirm_and_create",
] as const;

export default function OnboardingPage() {
  const router = useRouter();
  const [state, dispatch] = useReducer(onboardingReducer, initialOnboardingState);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inFlight = useRef(false);

  const send = useCallback(async (raw: string) => {
    const value = raw.trim();
    if (!value || inFlight.current) return;
    inFlight.current = true;
    setInput("");
    // Step 13: measure "user sends" → "AI reply visible" (target < 8s).
    mark("onboarding-send-start");
    dispatch({ type: "USER_MESSAGE", text: value });
    dispatch({ type: "AI_TYPING" });
    try {
      const res = await api.onboarding.message(value);
      // Hold the typing indicator for a natural beat before the reply lands.
      await new Promise((resolve) => setTimeout(resolve, typingDelayMs(res.reply)));
      dispatch({
        type: "AI_MESSAGE",
        text: res.reply,
        stage: res.stage,
        completed: Boolean(res.completed),
        requiresAuth: Boolean(res.requires_auth),
      });
      measureRoundtrip("onboarding-send-start", "onboarding-reply-visible", "onboarding_roundtrip");
    } catch {
      dispatch({ type: "ERROR", message: "Something went wrong — please try again." });
    } finally {
      inFlight.current = false;
    }
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [state.messages.length, state.status]);

  // Celebrate, then move into the dashboard.
  useEffect(() => {
    if (!state.completed) return;
    const timer = setTimeout(() => router.replace("/dashboard/chat" as Route), 2600);
    return () => clearTimeout(timer);
  }, [state.completed, router]);

  const busy = state.status !== "idle";
  const stageIndex = Math.max(0, STAGE_ORDER.indexOf(state.stage));
  const showCategoryGrid = state.stage === "category_select" && !busy;
  const showConfirm = state.stage === "confirm_and_create" && !state.completed;

  return (
    <div className="flex h-dvh flex-col bg-surface">
      {state.completed ? <Confetti /> : null}

      <header className="flex items-center justify-between border-b border-hairline px-6 py-4">
        <span className="font-display text-headline-sm text-ink">IIEVI</span>
        <span className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
          Setup · {Math.min(stageIndex + 1, 12)} / 12
        </span>
      </header>
      <div className="h-0.5 w-full bg-neutral" aria-hidden="true">
        <div
          className="h-full bg-ink transition-all duration-500"
          style={{ width: `${((stageIndex + 1) / 12) * 100}%` }}
        />
      </div>

      <div
        ref={scrollRef}
        className="mx-auto w-full max-w-2xl flex-1 overflow-y-auto px-4 py-6"
        role="log"
        aria-live="polite"
      >
        <ul className="flex flex-col gap-4">
          {state.messages.map((m) => (
            <li key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] whitespace-pre-wrap px-4 py-3 font-body text-body-sm ${
                  m.role === "user"
                    ? "bg-ink text-surface"
                    : "border border-hairline bg-neutral text-ink"
                }`}
              >
                {m.text}
              </div>
            </li>
          ))}
          {state.status === "typing" ? (
            <li className="flex justify-start">
              <TypingDots />
            </li>
          ) : null}
        </ul>

        {showCategoryGrid ? (
          <div className="mt-4">
            <CategoryGrid onSelect={(name) => void send(name)} disabled={busy} />
          </div>
        ) : null}

        {state.completed ? (
          <div className="mt-10 text-center">
            <p className="font-display text-headline-md text-ink">You&apos;re all set 🎉</p>
            <p className="mt-2 font-body text-body-sm text-graphite">
              Taking you to your dashboard…
            </p>
          </div>
        ) : null}

        {state.error ? (
          <p className="mt-4 text-center font-mono text-mono-sm text-signal" role="alert">
            {state.error}
          </p>
        ) : null}
      </div>

      {!state.completed ? (
        <div className="border-t border-hairline">
          <div className="mx-auto w-full max-w-2xl px-4 py-3">
            {state.requiresAuth ? (
              <div className="flex flex-col items-center gap-2 text-center">
                <p className="font-body text-body-sm text-graphite">
                  Please sign in to finish setting up your profile.
                </p>
                <ButtonLink href="/register">Create your account</ButtonLink>
              </div>
            ) : showConfirm ? (
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="font-body text-body-sm text-graphite">
                  Ready to bring your AI to life?
                </p>
                <Button onClick={() => void send("confirm")} disabled={busy}>
                  {busy ? "Creating…" : "Looks perfect"}
                </Button>
              </div>
            ) : (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void send(input);
                }}
                className="flex items-end gap-2"
              >
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void send(input);
                    }
                  }}
                  rows={1}
                  disabled={busy}
                  placeholder="Type your answer…"
                  aria-label="Your answer"
                  className="min-h-[46px] flex-1 resize-none border border-hairline bg-surface px-3 py-2.5 font-body text-body-sm text-ink outline-none transition-colors focus:border-signal disabled:opacity-60"
                />
                <button
                  type="submit"
                  disabled={busy || input.trim() === ""}
                  aria-label="Send"
                  className="inline-flex h-[46px] w-[46px] shrink-0 items-center justify-center border border-ink bg-ink text-surface transition-colors hover:bg-surface hover:text-ink disabled:opacity-40"
                >
                  <Send size={16} strokeWidth={1.75} aria-hidden="true" />
                </button>
              </form>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}

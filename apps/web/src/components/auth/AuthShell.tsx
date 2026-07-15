import { type ReactNode } from "react";

import { Pill } from "@/components/linen";

import { AuthSimulation } from "./AuthSimulation";

/** Split-screen auth layout: animated product demo on the left, form on the right. */
export function AuthShell({ children, headline }: { children: ReactNode; headline: string }) {
  return (
    <div className="grid min-h-screen md:grid-cols-2">
      <aside
        aria-label="Product demonstration"
        className="hidden flex-col justify-between border-r border-hairline bg-neutral p-10 md:flex"
      >
        <span className="font-display text-headline-sm text-ink">IIEVI</span>
        <div className="flex flex-col gap-6">
          <Pill variant="signal">Live demo</Pill>
          <p className="max-w-sm font-display text-headline-md text-ink">{headline}</p>
          <AuthSimulation />
        </div>
        <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
          One chat. Every business task.
        </p>
      </aside>
      <main className="flex items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-sm">{children}</div>
      </main>
    </div>
  );
}

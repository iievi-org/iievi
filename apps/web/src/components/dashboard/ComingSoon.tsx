import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Pill } from "@/components/linen";

interface ComingSoonProps {
  icon: LucideIcon;
  eyebrow: string;
  title: string;
  description: string;
  bullets?: string[];
  note?: string;
  /** Optional CTA row rendered beneath the note (e.g. ButtonLinks). */
  children?: ReactNode;
}

/**
 * A restrained, Linen-styled placeholder for dashboard surfaces whose backend
 * is still being built. Vertically centered, hairline-accented, generous
 * whitespace — an "empty state" that reads as intentional, not broken.
 */
export function ComingSoon({
  icon: Icon,
  eyebrow,
  title,
  description,
  bullets,
  note,
  children,
}: ComingSoonProps) {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-6">
      <div className="flex w-full max-w-md flex-col items-center text-center">
        <Pill>{eyebrow}</Pill>

        <Icon
          size={40}
          strokeWidth={1.25}
          aria-hidden
          className="mt-8 text-stone"
        />

        <h1 className="mt-6 font-display text-headline-lg text-ink">{title}</h1>

        <p className="mt-4 font-body text-body-md text-graphite">{description}</p>

        {bullets && bullets.length > 0 ? (
          <ul className="mt-8 flex flex-col gap-3 text-left">
            {bullets.map((bullet) => (
              <li key={bullet} className="flex items-start gap-3 font-body text-body-sm text-graphite">
                <span
                  aria-hidden
                  className="mt-[0.45rem] h-1.5 w-1.5 shrink-0 rounded-full bg-signal"
                />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        ) : null}

        {note ? (
          <p className="mt-8 font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            {note}
          </p>
        ) : null}

        {children ? (
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">{children}</div>
        ) : null}
      </div>
    </div>
  );
}

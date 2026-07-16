"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { type ReactNode, useId } from "react";

import { LINEN_EASE } from "@/lib/animations";

interface AccordionPanelProps {
  title: string;
  /** Optional short line under the title (e.g. count / status). */
  summary?: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}

/**
 * A single controlled accordion panel, Linen-styled. Accessible: the header is a
 * real button wired with aria-expanded / aria-controls, and the region is
 * labelled by the header. Framer Motion animates the height reveal.
 */
export function AccordionPanel({ title, summary, open, onToggle, children }: AccordionPanelProps) {
  const baseId = useId();
  const headerId = `${baseId}-header`;
  const regionId = `${baseId}-region`;

  return (
    <div className="border border-hairline bg-transparent">
      <h3 className="m-0">
        <button
          type="button"
          id={headerId}
          aria-expanded={open}
          aria-controls={regionId}
          onClick={onToggle}
          className="flex w-full items-center justify-between gap-4 px-6 py-5 text-left transition-colors hover:bg-neutral focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-signal"
        >
          <span className="flex flex-col gap-1">
            <span className="font-display text-headline-sm text-ink">{title}</span>
            {summary ? (
              <span className="font-body text-body-sm text-stone">{summary}</span>
            ) : null}
          </span>
          <ChevronDown
            aria-hidden="true"
            size={20}
            strokeWidth={1.5}
            className={`shrink-0 text-graphite transition-transform duration-200 ${
              open ? "rotate-180" : ""
            }`}
          />
        </button>
      </h3>

      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            key="content"
            id={regionId}
            role="region"
            aria-labelledby={headerId}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: LINEN_EASE }}
            className="overflow-hidden"
          >
            <div className="border-t border-hairline px-6 py-6">{children}</div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

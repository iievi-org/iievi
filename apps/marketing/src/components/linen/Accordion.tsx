import { useState, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Plus, Minus } from "lucide-react";

interface Item {
  question: ReactNode;
  answer: ReactNode;
}

export function Accordion({ items }: { items: Item[] }) {
  const [open, setOpen] = useState<number | null>(null);
  const reduce = useReducedMotion();
  return (
    <div className="w-full">
      {items.map((it, i) => {
        const isOpen = open === i;
        return (
          <div key={i} className="border-b border-hairline">
            <button
              onClick={() => setOpen(isOpen ? null : i)}
              className="w-full flex items-center justify-between gap-6 py-6 text-left cursor-pointer group"
              aria-expanded={isOpen}
            >
              <span className="font-body text-headline-sm font-medium text-ink">{it.question}</span>
              <span className="shrink-0 text-ink">
                {isOpen ? (
                  <Minus size={20} strokeWidth={1.5} />
                ) : (
                  <Plus size={20} strokeWidth={1.5} />
                )}
              </span>
            </button>
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  initial={reduce ? false : { height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={reduce ? { opacity: 0 } : { height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="overflow-hidden"
                >
                  <div className="pb-6 pr-12 font-body text-body-sm text-graphite max-w-3xl">
                    {it.answer}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}

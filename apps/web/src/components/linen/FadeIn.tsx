"use client";

import { motion, useReducedMotion } from "framer-motion";
import { type ReactNode } from "react";

import { LINEN_EASE } from "@/lib/animations";

/** Scroll-triggered fade-up. Renders statically when reduced motion is on. */
export function FadeIn({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.4, delay, ease: LINEN_EASE }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

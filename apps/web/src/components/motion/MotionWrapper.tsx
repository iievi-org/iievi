"use client";

import { motion, useReducedMotion, type Variants } from "framer-motion";
import { type ReactNode } from "react";

import { fadeUp } from "@/lib/animations";

/**
 * Wrap any section to add a scroll-triggered entrance (whileInView, once,
 * -50px margin). Honours prefers-reduced-motion by rendering statically
 * (WCAG 2.1 AA).
 */
export function MotionWrapper({
  children,
  className,
  variants = fadeUp,
}: {
  children: ReactNode;
  className?: string;
  variants?: Variants;
}) {
  const reduce = useReducedMotion();
  if (reduce) return <div className={className}>{children}</div>;
  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, margin: "-50px" }}
      variants={variants}
    >
      {children}
    </motion.div>
  );
}

"use client";

import { motion, useReducedMotion } from "framer-motion";

const COLORS = ["#c8462c", "#111111", "#3f8f5b", "#b8791f", "#2f6f9f"];

/** A one-shot Framer Motion confetti burst for the onboarding celebration. */
export function Confetti({ count = 64 }: { count?: number }) {
  const reduce = useReducedMotion();
  if (reduce) return null;

  const pieces = Array.from({ length: count }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    color: COLORS[i % COLORS.length] ?? "#111111",
    delay: Math.random() * 0.3,
    duration: 1.8 + Math.random() * 1.2,
    rotate: (Math.random() - 0.5) * 720,
    drift: (Math.random() - 0.5) * 140,
  }));

  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-50 overflow-hidden">
      {pieces.map((p) => (
        <motion.span
          key={p.id}
          initial={{ y: "-10vh", opacity: 1, rotate: 0 }}
          animate={{ y: "110vh", x: p.drift, rotate: p.rotate, opacity: [1, 1, 0] }}
          transition={{ duration: p.duration, delay: p.delay, ease: "easeIn" }}
          style={{
            position: "absolute",
            top: 0,
            left: `${p.left}%`,
            width: 8,
            height: 8,
            backgroundColor: p.color,
          }}
        />
      ))}
    </div>
  );
}

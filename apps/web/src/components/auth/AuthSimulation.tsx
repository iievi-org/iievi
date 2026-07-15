"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";

import { LINEN_EASE } from "@/lib/animations";

const SCRIPT = [
  { role: "customer", text: "Hi, do you do deep cleaning for a 2BHK?" },
  {
    role: "ai",
    text: "We do! A 2BHK deep clean is ₹2,500–₹4,500 and takes about 4 hours. When suits you?",
  },
  { role: "customer", text: "This Saturday morning?" },
  {
    role: "ai",
    text: "Saturday 9am is open. Shall I lock it in? 10% off applies to your first booking.",
  },
  { role: "customer", text: "Yes please!" },
  { role: "ai", text: "Booked ✓ You'll get a WhatsApp confirmation. See you Saturday!" },
] as const;

/** A scripted home-cleaning AI conversation that plays out on the auth screen. */
export function AuthSimulation() {
  const reduce = useReducedMotion();
  const [count, setCount] = useState(reduce ? SCRIPT.length : 0);

  useEffect(() => {
    if (reduce || count >= SCRIPT.length) return;
    const timer = setTimeout(() => setCount((c) => c + 1), count === 0 ? 500 : 1200);
    return () => clearTimeout(timer);
  }, [count, reduce]);

  return (
    <div className="flex flex-col gap-3" aria-hidden="true">
      {SCRIPT.slice(0, count).map((message, i) => (
        <motion.div
          key={i}
          initial={reduce ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: LINEN_EASE }}
          className={`max-w-[85%] border border-hairline px-4 py-3 font-body text-body-sm ${
            message.role === "ai" ? "self-start bg-neutral text-ink" : "self-end bg-ink text-surface"
          }`}
        >
          {message.text}
        </motion.div>
      ))}
    </div>
  );
}

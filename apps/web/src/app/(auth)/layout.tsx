import { type ReactNode } from "react";

/** Minimal shell for auth pages — no navigation; the pages own their layout. */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-surface">{children}</div>;
}

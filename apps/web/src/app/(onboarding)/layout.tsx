import { type ReactNode } from "react";

/** Full-screen, distraction-free shell for the onboarding flow (no navigation). */
export default function OnboardingLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-screen bg-surface">{children}</div>;
}

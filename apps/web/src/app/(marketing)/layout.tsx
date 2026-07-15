import Link from "next/link";
import { type ReactNode } from "react";

/** Marketing shell: sticky glass nav + footer (the full site lives in apps/marketing). */
export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-surface">
      <header
        className="sticky top-0 z-30 border-b border-hairline backdrop-blur"
        style={{ backgroundColor: "color-mix(in srgb, var(--surface) 82%, transparent)" }}
      >
        <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-4 md:px-10">
          <Link href="/" className="font-display text-headline-sm text-ink">
            IIEVI
          </Link>
          <Link
            href="/login"
            className="font-body text-label-sm uppercase tracking-[0.14em] text-ink"
          >
            Sign in
          </Link>
        </div>
      </header>
      <main>{children}</main>
      <footer className="border-t border-hairline">
        <div className="mx-auto max-w-[1280px] px-6 py-10 md:px-10">
          <p className="font-mono text-mono-sm uppercase tracking-[0.14em] text-stone">
            © IIEVI — One Chat. Every Business Task.
          </p>
        </div>
      </footer>
    </div>
  );
}

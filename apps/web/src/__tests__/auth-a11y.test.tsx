import { render } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";

import LoginPage from "@/app/(auth)/login/page";
import RegisterPage from "@/app/(auth)/register/page";

// The auth pages call useRouter() at the top level; stub the App Router so they
// render outside a real navigation context. next/link becomes a plain anchor.
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: vi.fn(),
    push: vi.fn(),
    prefetch: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("next/link", () => ({
  __esModule: true,
  default: ({
    href,
    children,
    className,
  }: {
    href: string;
    children: ReactNode;
    className?: string;
  }) => (
    <a href={href} className={className}>
      {children}
    </a>
  ),
}));

// color-contrast needs a real rendering engine (canvas); jsdom can't compute it,
// so verify it visually. Everything else — labels, roles, landmarks — runs here.
const AXE_OPTIONS = { rules: { "color-contrast": { enabled: false } } };

describe("auth pages accessibility", () => {
  it("login page has no WCAG violations", async () => {
    const { container } = render(<LoginPage />);
    expect(await axe(container, AXE_OPTIONS)).toHaveNoViolations();
  });

  it("register page has no WCAG violations", async () => {
    const { container } = render(<RegisterPage />);
    expect(await axe(container, AXE_OPTIONS)).toHaveNoViolations();
  });
});

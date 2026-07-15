import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, expect } from "vitest";

// vitest-axe's matcher registration ships as an empty module and its type
// exports don't merge with vitest v2, so register + type the matcher here.
// It only needs to read `violations` off an axe results object.
interface AxeLikeResults {
  violations: Array<{ id: string; help: string; nodes: unknown[] }>;
}

expect.extend({
  toHaveNoViolations(received: AxeLikeResults) {
    const violations = received.violations ?? [];
    const pass = violations.length === 0;
    return {
      pass,
      actual: violations,
      message: () =>
        pass
          ? "expected accessibility violations, but found none"
          : `expected no accessibility violations, found ${violations.length}:\n` +
            violations
              .map((v) => `  • [${v.id}] ${v.help} — ${v.nodes.length} node(s)`)
              .join("\n"),
    };
  },
});

declare module "vitest" {
  // Type params must match vitest's own `Assertion<T = any>` to merge.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  interface Assertion<T = any> {
    toHaveNoViolations(): T;
  }
  interface AsymmetricMatchersContaining {
    toHaveNoViolations(): unknown;
  }
}

// jsdom omits these; framer-motion's reduced-motion + layout hooks reach for them.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
if (!("ResizeObserver" in globalThis)) {
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
}

afterEach(() => {
  cleanup();
});

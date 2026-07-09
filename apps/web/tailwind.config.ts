import type { Config } from "tailwindcss";

/**
 * Linen design system tokens, ported from apps/marketing/src/styles.css.
 * That file is the source of truth — keep the two in sync.
 * Rules: no gradients, no shadows, zero border-radius (pills excepted).
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      surface: "var(--surface)",
      neutral: "var(--neutral)",
      ink: "var(--primary)",
      graphite: "var(--secondary)",
      stone: "var(--tertiary)",
      hairline: "var(--border)",
      signal: "var(--focus)",
    },
    borderRadius: {
      none: "0",
      DEFAULT: "0",
      full: "9999px",
    },
    fontFamily: {
      display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
      body: ["var(--font-body)", "ui-sans-serif", "system-ui", "sans-serif"],
      mono: ["var(--font-mono)", "ui-monospace", "monospace"],
    },
    extend: {
      fontSize: {
        "display-xl": ["120px", { lineHeight: "0.92", letterSpacing: "-0.01em", fontWeight: "700" }],
        "display-lg": ["88px", { lineHeight: "0.96", letterSpacing: "-0.005em", fontWeight: "700" }],
        "headline-lg": ["56px", { lineHeight: "1", fontWeight: "700" }],
        "headline-md": ["28px", { lineHeight: "1.1", fontWeight: "600" }],
        "headline-sm": ["18px", { lineHeight: "1.3", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "1.55", fontWeight: "400" }],
        "body-sm": ["14px", { lineHeight: "1.55", fontWeight: "400" }],
        "label-sm": ["11px", { lineHeight: "1.2", letterSpacing: "0.14em", fontWeight: "500" }],
        "mono-sm": ["11px", { lineHeight: "1.3", letterSpacing: "0.04em", fontWeight: "400" }],
        "stat-numeral": ["56px", { lineHeight: "1", letterSpacing: "-0.01em", fontWeight: "700" }],
      },
      letterSpacing: {
        label: "0.14em",
        mono: "0.04em",
      },
    },
  },
  plugins: [],
};

export default config;

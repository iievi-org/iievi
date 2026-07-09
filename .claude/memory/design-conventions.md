# IIEVI Design Conventions — "Linen" Design System

**Source of truth:** `iievi-web/` (the marketing landing page). Its `src/styles.css` and
`src/components/linen/` are the PRIMARY design reference for every component in the whole
project — dashboard, chat UI, onboarding, everything. When in doubt, open those files.

**Note:** This supersedes the setup document's mention of Geist fonts. The Linen system
uses Archivo Narrow / Inter / JetBrains Mono.

## Philosophy
Single-mode editorial system. **No gradients. No shadows. No rounded corners** (`--radius: 0`
everywhere; the only exception is `Pill`, which is `rounded-full`). Hierarchy comes from
type, scale, whitespace, and hairline borders — not color or elevation.

## Palette (CSS custom properties in `:root`, dark via `[data-theme="dark"]`)
| Token | Light | Role |
|---|---|---|
| `--surface` | `#f1ede3` | page background (linen) |
| `--neutral` | `#f7f4ec` | inset/paper background |
| `--primary` / ink | `#111111` | headings, primary buttons |
| `--secondary` / graphite | `#3a3733` | body text (html/body default color) |
| `--tertiary` / stone | `#8a857c` | labels, muted text |
| `--border` / hairline | `#1f1d1a` | all borders (1px hairlines) |
| `--focus` / signal | `#c8462c` | ONLY accent — focus rings, errors, highlights |

Tailwind color names: `surface`, `neutral`, `ink`, `graphite`, `stone`, `hairline`, `signal`.
Dark mode exists via `[data-theme="dark"]` attribute (not `.dark` class); `color-scheme` set on html.
Selection style: inverted (ink background, surface text).

## Typography
- `font-display`: **Archivo Narrow** — all headings (h1–h6 default to it, weight 700, ink color)
- `font-body`: **Inter** — body copy
- `font-mono`: **JetBrains Mono** — labels, stats captions, meta text
- Named type scale (use these, not ad-hoc sizes): `text-display-xl` (120px/0.92), `text-display-lg`
  (88px), `text-headline-lg` (56px), `text-headline-md` (28px), `text-headline-sm` (18px),
  `text-body-md` (16px/1.55), `text-body-sm` (14px), `text-label-sm` (11px, tracking 0.14em),
  `text-mono-sm` (11px, tracking 0.04em), `text-stat-numeral` (56px)
- Mobile overrides at ≤768px: display-xl→64px, display-lg→52px, headline-lg→36px
- Labels/buttons are ALWAYS `uppercase tracking-[0.14em]` at `text-label-sm`

## Component idioms (`src/components/linen/`)
- **Button** — variants `primary` (ink bg, inverts to surface on hover), `ghost` (transparent,
  hairline border, fills ink on hover), `ghost-inverse`. Square corners, uppercase label text,
  `px-[18px] py-[12px]`, `focus-visible:outline-signal`. Also `ButtonLink`/`ButtonAnchor` wrappers.
- **Card** — `border border-hairline p-8`; variants `open` (transparent) / `paper` (`bg-neutral`)
- **Container** — `max-w-[1280px] mx-auto px-6 md:px-10`
- **Section** — `py-16 md:py-24`, optional `inset` (bg-neutral band)
- **Rule** — horizontal hairline `<hr>` used as a structural divider
- **SectionLabel** — mono, uppercase, stone-colored kicker above headings
- **Pill** — rounded-full tag; variants `outline` / `ink` / `signal`
- **Stat** — big display numeral over mono caption, hairline bottom border, counts up on
  scroll-into-view (respects `useReducedMotion`, Indian locale formatting `en-IN`)
- **Input** — underline style: transparent bg, top+bottom hairline only, `px-0`,
  focus = 2px signal bottom border; label is uppercase label-sm in stone; error in mono signal
- **FadeIn** — standard entrance: `opacity 0→1, y 16→0`, 0.4s, ease `[0.22, 1, 0.36, 1]`,
  `whileInView` once with `-60px` margin, honors reduced motion

## Motion rules
- Framer Motion; every animation must respect `useReducedMotion`
- Entrances: FadeIn pattern above. Marquee: 40s linear, pauses on hover
- Transitions: `transition-colors duration-150` on interactive elements

## Copy/tone (from landing page)
Tagline: "One Chat. Every Business Task." Direct, numbers-forward copy (stats like "3s", "₹138"),
Indian business context (Diwali, ₹, en-IN formatting), en/hi i18n via i18next.

## When building new UI (dashboard, chat, etc.)
1. Reuse the linen primitives' class recipes verbatim where possible.
2. Never introduce: border radii (except pills), drop shadows, gradients, new accent colors.
3. New tokens go into the `@theme` block as CSS custom properties, both light and dark values.
4. shadcn/ui primitives are allowed but must be restyled through the alias tokens already
   mapped in `styles.css` (`--color-background`, `--color-ring: signal`, etc.).

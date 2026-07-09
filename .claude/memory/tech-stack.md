# IIEVI Tech Stack Reference

## Backend (`apps/api`)
- FastAPI, Python 3.12, fully async (`async def` everywhere)
- SQLAlchemy 2.0 async ORM with typed `Mapped[]` columns; Alembic migrations
- PostgreSQL 16 on Neon.tech — RLS on every tenant-scoped table
  - Policy: `USING (tenant_id = current_setting('app.current_tenant_id')::uuid)`
  - Session var set per request: `SELECT set_config('app.current_tenant_id', $1, true)`
  - Exception: `platform_identifiers` has NO RLS (webhook routing pre-tenant-context)
- Celery + Redis (broker and result backend); six named queues:
  `ai_conversations`, `post_publishing`, `creative_generation`, `lead_outreach`, `ad_management`, `usage_tracking`
- AI: Anthropic Python SDK — Claude Haiku 3.5 (`claude-haiku-3-5-20251001`) for conversations, Claude Sonnet 4 (`claude-sonnet-4-20250514`) for generation; LangFuse traces every AI call
- Images: NanoBanana Pro API. Social APIs: httpx (async)
- Payments: Razorpay (India) + Stripe (international) — hosted pages only (PCI DSS SAQ-A)
- Secrets: Doppler. Errors: Sentry. Logs: Axiom
- Infra: Hetzner CX32 (4 vCPU / 8GB, Singapore) — nginx, Supervisor, Redis
- Media: Cloudflare R2 (S3-compatible), signed URLs (15 min display / 10 min publishing)
- Email: Resend. Uptime: Uptime Robot

## Frontend (`apps/web`)
- Next.js 14 App Router, TypeScript strict (`noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`)
- Tailwind CSS + CSS custom properties for theming; shadcn/ui; Tremor charts
- TanStack Query v5 for all server state; React Hook Form + Zod resolver for all forms
- Framer Motion
- Fonts: Archivo Narrow (display) / Inter (body) / JetBrains Mono — per the Linen design
  system in `iievi-web/` (overrides the setup doc's Geist mention; see design-conventions.md)

## Monorepo (Turborepo)
- `iievi-web/` — EXISTING marketing landing page (TanStack Start + Vite + Bun, Tailwind v4,
  Lovable-generated). It is the marketing webfront AND the primary design reference (Linen
  design system) for the whole project. Do not rebuild it; fold it in as the marketing app.
- `packages/api-client` — typed fetch functions, must stay React Native-portable
- `packages/types` — TS interfaces for all API shapes
- `packages/validators` — Zod schemas for forms and API contracts
- `packages/constants` — category configs, plan limits, platform enums
- CI: `.github/workflows/ci.yml` (blocks merge), `deploy.yml` (Hetzner + Vercel on main)

## Data conventions
- Money in paise (integer). Timestamps TIMESTAMPTZ. PKs UUID via `gen_random_uuid()`. Enums are native PostgreSQL ENUM types.

## Plans
Trial (free, limited) → Starter ₹2,999/mo → Growth ₹6,999/mo → Agency ₹14,999/mo.
Customers bring their own Anthropic / NanoBanana Pro / social credentials.

## Canva
Platform-owned Canva API key comes in the NEXT update. Mark integration points with
`[CANVA_NEXT_UPDATE]` comments — do NOT implement now.

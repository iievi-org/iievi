# IIEVI Workflow Rules

1. **Build in dependency order.** The 10 instruction prompts are sequential. Never implement a later prompt's feature in an earlier session. Security and data layers are verified before any feature is built on them. Verify first, build second.
2. **Definition of Done tests run before ending every session.** A prompt is not complete until its DoD checks pass.
3. **Git conventions**
   - Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
   - Branches: `feature/`, `fix/`, `chore/`
   - No direct commits to main; squash merges only
   - Every PR includes a test that verifies the changed behaviour
4. **All async work goes through Celery.** No long-running operation inside an API request. Webhook handlers return HTTP 200 within 200ms and enqueue.
5. **Idempotency everywhere it matters.** Webhooks deduped via `webhook_events` (platform event ID). Publishing/messaging tasks check record state before acting. Billing deduped by provider event ID. Payments use idempotency keys.
6. **AI outputs are never trusted raw.** Grounded system prompts (tenant profile only, explicit prohibitions), Pydantic validation before DB writes, hallucination test suite in CI.
7. **Circuit breakers wrap every external API call** (Anthropic, Meta, WhatsApp, NanoBanana Pro) using the `circuitbreaker` library.
8. **Feature flags** via `FeatureFlagService` — Redis (fast) + `feature_flags` table (persistent). Frontend reads from `GET /billing/capabilities`.
9. **Caching:** tenant context 5 min in Redis (invalidate on profile update); heavy analytics 1 h; static config compiled into the JS bundle; TanStack Query stale-while-revalidate on the frontend.
10. **Shared packages stay portable** — nothing in `packages/*` may depend on Next.js or the DOM; they must work in React Native later.

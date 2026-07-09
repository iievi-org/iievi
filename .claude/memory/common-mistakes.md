# IIEVI Common Mistakes to Avoid

1. **Building features before the security/data layer is verified.** The #1 failure mode named in the setup doc. Do not scaffold features on unverified RLS/auth.
2. **Forgetting RLS on a new table.** Every tenant-scoped table needs the policy; only `platform_identifiers` is exempt (webhook routing). Add an automated check/migration test rather than relying on memory.
3. **Running long work synchronously in a request.** Anything slow (AI calls, publishing, image generation) belongs in a Celery queue. Webhooks must ACK < 200ms.
4. **Storing money as floats or rupees.** Always integer paise.
5. **Trusting AI output.** Never write Claude output to the DB without Pydantic schema validation. Never let prompts include data outside the tenant's profile.
6. **Leaking tenant context.** Don't cache tenant-scoped data under a global key; don't run queries before `set_config('app.current_tenant_id', ...)` is applied.
7. **Duplicate webhook processing.** Always check `webhook_events` by platform event ID before handling; billing webhooks deduped by provider event ID.
8. **Refresh tokens in localStorage / access tokens in cookies.** Access token lives in memory only; refresh token in HttpOnly Secure SameSite=Strict cookie only.
9. **Direct external API calls without a circuit breaker** — one Meta outage must not pile up the queues.
10. **Implementing Canva now.** Only leave `[CANVA_NEXT_UPDATE]` markers.
11. **Breaking package portability.** No Next.js/DOM imports inside `packages/*` (future React Native app).
12. **Updating or deleting audit_log rows.** Append-only, no exceptions.
13. **Using `Any` (Python) or `any` (TypeScript).** Both are banned by convention.
14. **Committing directly to main / non-conventional commit messages.**
15. **Skipping DoD tests at session end.** Each instruction prompt's Definition of Done must pass before moving on.

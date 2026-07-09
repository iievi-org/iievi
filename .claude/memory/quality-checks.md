# IIEVI Quality Checks

Run before ending any session / merging any PR.

## Security (three-layer tenant isolation)
- [ ] Every new tenant-scoped table: `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE` + RLS policy enabled
- [ ] Application layer uses `with_tenant_scope()` wrapper
- [ ] JWT carries `sub`, `tid`, `plan`, `admin`; access token 15 min in memory; refresh 30 days HttpOnly/Secure/SameSite=Strict cookie; Redis JTI blacklist works
- [ ] Sensitive credentials encrypted AES-256-GCM at the app layer, stored as `base64(iv):base64(ciphertext_with_auth_tag)`; master key only in Doppler
- [ ] `require_plan()` gating applied to plan-restricted routes
- [ ] Rate limits in place: 200 req/min global IP, 100 req/min per tenant, 20 AI calls/hour per tenant
- [ ] Audit log entries written for every create/update/delete/auth event; table remains append-only

## Code quality
- [ ] Python: full type hints incl. returns, `Annotated` DI, Pydantic v2, no `Any`, module docstrings
- [ ] TypeScript: strict, no `any`, discriminated unions for variants, API types in `packages/types`
- [ ] Error responses shaped `{code, message, details}`; 4xx → WARNING, 5xx → ERROR + Sentry with tenant_id
- [ ] Typed custom exceptions / Error subclasses only

## Tests & CI
- [ ] Test accompanying every behaviour change
- [ ] Hallucination test suite passes
- [ ] CI (lint, type-check, tests) green — merge is blocked otherwise
- [ ] RLS isolation tests: tenant A can never read tenant B's rows through any endpoint

## Compliance targets
OWASP Top 10 · ISO 27001 · GDPR Art. 25 (privacy by design) · PCI DSS SAQ-A (no raw card data ever)

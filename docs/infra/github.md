# GitHub Repository & Branch Protection

## Create org + repo

Organisation creation is web-only: https://github.com/organizations/plan
(create org, e.g. `iievi-hq`). Then from the monorepo root:

```bash
gh repo create <ORG>/iievi --private --source . --push
```

## Branch protection on main — set these three rules on day one

```bash
gh api -X PUT repos/<ORG>/iievi/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["api (ruff, mypy, pytest)", "web (tsc, eslint, tests, build)"]
  },
  "required_pull_request_reviews": { "required_approving_review_count": 1 },
  "enforce_admins": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "restrictions": null
}
JSON
```

Also in Settings → General: enable **squash merging only** (disable merge
commits and rebase merging).

## Repository secrets (Settings → Secrets → Actions)

| Secret | Purpose |
|---|---|
| `DOPPLER_TOKEN` | Doppler service token (prd config) for deploy.yml |
| `VPS_HOST` | Hetzner VPS IP/hostname |
| `VPS_SSH_KEY` | Private key of a dedicated deploy keypair |
| `API_BASE_URL` | `https://api.<domain>` for post-deploy verification |
| `VERCEL_DEPLOY_HOOK` | Vercel deploy hook URL for the frontend |

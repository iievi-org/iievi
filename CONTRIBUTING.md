# Contributing to IIEVI

## Prerequisites

Install these before anything else:

| Tool | Version | Install (macOS) |
|---|---|---|
| Node.js | 22.13+ | `brew install node@22` |
| pnpm | 9+ | `brew install pnpm` |
| Python | 3.12 | `brew install python@3.12` |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| podman | 5+ | `brew install podman && podman machine init && podman machine start` |
| Doppler CLI | latest | `brew install dopplerhq/cli/doppler` |

You also need to be invited to the Doppler `iievi` project (ask a maintainer).

## First-time setup — exactly 6 commands

```bash
git clone git@github.com:<ORG>/iievi.git && cd iievi   # 1. clone
doppler login                                           # 2. authenticate with Doppler
doppler setup --project iievi --config dev              # 3. bind this repo to the dev config
pnpm install                                            # 4. install JS/TS dependencies
(cd apps/api && uv sync)                                # 5. install Python dependencies
make up                                                 # 6. start the full local stack
```

Verify: `curl localhost:8000/health` returns `{"status":"ok",...}`.

There are **no .env files** in this project — Doppler injects all secrets at
runtime. If a command fails with "FATAL: invalid or missing environment
configuration", you are not running it under Doppler (`make <target>` handles
this for you).

## Port map

| Service | Port | Notes |
|---|---|---|
| FastAPI API | 8000 | hot-reload via uvicorn |
| Next.js web | 3000 | `pnpm --filter @iievi/web dev` |
| Marketing site | 5173 | `pnpm --filter @iievi/marketing dev` |
| PostgreSQL 16 | 5432 | user `iievi` / db `iievi`; app connects as `iievi_app` (RLS enforced) |
| Redis 7 | 6379 | Celery broker + cache |
| Flower | 5555 | Celery monitoring — 127.0.0.1 only |

## Running tests

```bash
make test        # everything
make test-api    # Python: pytest with coverage
make test-web    # TypeScript: vitest component tests via turbo
make lint        # ruff + eslint
make typecheck   # mypy (strict) + tsc --noEmit
```

## Database migrations

```bash
make migration m="add leads table"   # create (autogenerate against models)
make migrate                          # apply to your local database
```

Rules: migrations run **before** service restarts in deployment; every
tenant-scoped table must ship with its RLS policy in the same migration.

### Zero-downtime migration checklist

Migrations deploy BEFORE the new code restarts, so the OLD code must work
against the NEW schema. Before creating any migration that touches existing
columns, walk this checklist:

**Always safe (single deploy):**
- [ ] Adding a NULLABLE column (or one with a server default)
- [ ] Adding a new table
- [ ] Adding an index — but only with `CREATE INDEX CONCURRENTLY` inside
      `op.get_context().autocommit_block()`

**Never in a single deploy — requires the three-phase pattern:**
dropping a column/table, renaming a column, changing a column type.

1. **Phase 1 (expand):** add the new column; deploy code that WRITES to both
   old and new but still READS the old.
2. **Phase 2 (migrate):** backfill the new column; verify counts match;
   deploy code that reads the new column.
3. **Phase 3 (contract):** only after Phase 2 has been live and verified,
   drop the old column in its own migration.

Also check:
- [ ] Does the migration take locks a live table can't afford?
      (`ALTER TABLE ... SET NOT NULL` scans; adding a column with a volatile
      default rewrites the table.)
- [ ] Is `downgrade()` real, or is this migration forward-only? (Forward-only
      is fine — say so in the docstring; production never runs `downgrade`.)
- [ ] New tenant-scoped table → RLS policy in the SAME migration.

## Adding an environment variable

1. Add it to Doppler in **all three configs** (`dev`, `stg`, `prd`):
   `doppler secrets set MY_VAR --config dev` (repeat for stg/prd).
2. Add the typed field to `apps/api/app/core/config.py` (required = no default).
3. If the compose stack needs it, map it in `podman-compose.yml`.
4. Document it in `docs/infra/doppler.md`.

Never create a `.env` file. `.gitignore` blocks `*.env*` globally.

## Dependency updates (monthly, never auto-merged)

1. `cd apps/api && uv lock --upgrade` and, at the root, `pnpm update -r`.
2. Review the lockfile diffs and the changelogs of anything with a major bump.
3. Run the full suite (`make test`, `make lint`, `make typecheck`).
4. Open a `chore/dependency-bumps-YYYY-MM` PR. CI runs pip-audit, pnpm audit,
   and Snyk on it. **Never** auto-merge dependency updates — a green build
   does not prove a breaking behaviour change didn't land.

Security scanning runs on every PR: pip-audit (PyPI Advisory DB, strict),
`pnpm audit --audit-level high`, and Snyk (when `SNYK_TOKEN` is configured).
Any known vulnerability blocks the merge.

## Branch and PR conventions

- Branches: `feature/<slug>`, `fix/<slug>`, `chore/<slug>`
- Commits: Conventional Commits — `feat:`, `fix:`, `chore:`, `docs:`
- No direct commits to `main` (branch protection enforces this)
- Every PR must include a test verifying the changed behaviour
- Squash merges only; CI (ruff, mypy, pytest, tsc, eslint, vitest) must be green

## If this document failed you

This file is contractually "tested by someone who has never seen the
codebase". If you got stuck following it, that is a bug — open a PR fixing
the step that failed you.

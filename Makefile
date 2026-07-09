# IIEVI developer commands. Everything runs under Doppler so no .env files
# ever exist locally. First run: `doppler setup` (select project iievi, config dev).

.PHONY: help up down logs api-shell db-shell test test-api test-web lint typecheck migrate migration fmt

help: ## List available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up: ## Start the full local stack (Postgres, Redis, API, worker, beat, Flower)
	doppler run -- podman compose -f podman-compose.yml up --build -d

down: ## Stop the local stack
	podman compose -f podman-compose.yml down

logs: ## Tail logs from all services
	podman compose -f podman-compose.yml logs -f

api-shell: ## Shell inside the running API container
	podman compose -f podman-compose.yml exec api bash

db-shell: ## psql into the local database (as owner role)
	podman compose -f podman-compose.yml exec postgres psql -U iievi -d iievi

test: test-api test-web ## Run all test suites

test-api: ## Run the Python test suite with coverage
	cd apps/api && doppler run -- uv run pytest

test-web: ## Run frontend and package tests
	doppler run -- pnpm turbo run test

lint: ## Lint everything (ruff + eslint)
	cd apps/api && uv run ruff check .
	pnpm turbo run lint

typecheck: ## Type-check everything (mypy + tsc)
	cd apps/api && doppler run -- uv run mypy app
	pnpm turbo run typecheck

migrate: ## Apply Alembic migrations (owner role URL from Doppler)
	cd apps/api && doppler run -- uv run alembic upgrade head

migration: ## Create a new Alembic migration: make migration m="add leads table"
	cd apps/api && doppler run -- uv run alembic revision --autogenerate -m "$(m)"

fmt: ## Format all code
	cd apps/api && uv run ruff format .
	pnpm format

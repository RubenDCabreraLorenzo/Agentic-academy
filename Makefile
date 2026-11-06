.PHONY: dev-secrets setup up test e2e content

dev-secrets:
	python3 scripts/dev_secrets.py

content:
	uv run --project backend academy content validate --run-solutions
	uv run --project backend academy content build --lang en --out dist/content

setup: dev-secrets
	docker compose up -d --wait db mailpit
	uv sync --project backend
	uv sync --project runner
	uv run --project backend alembic -c backend/alembic.ini upgrade head
	$(MAKE) content
	docker build -t academy-sandbox:dev runner/sandbox-image
	pnpm --dir frontend install
	pnpm --dir frontend generate:api

up:
	docker compose up --build api runner web

test:
	uv run --project backend pytest backend/tests
	uv run --project runner pytest runner/tests/unit
	uv run --project runner pytest runner/sandbox-image/academy_sim/tests
	pnpm --dir frontend test

e2e:
	pnpm --dir frontend e2e

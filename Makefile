.PHONY: test lint typecheck fmt check pipeline frontend-dev frontend-build frontend-test frontend-lint

# ── pipeline ──────────────────────────────────────────────────────────────────

test:
	cd pipeline && uv run pytest -q

lint:
	cd pipeline && uv run ruff check .

typecheck:
	cd pipeline && uv run mypy .

fmt:
	cd pipeline && uv run ruff check --fix .
	cd pipeline && uv run ruff format .

# Run all read-only checks (CI gate).
check: lint typecheck test
	cd pipeline && uv run ruff format --check .

pipeline:
	cd pipeline && uv run python -m riksdagen

# ── frontend ──────────────────────────────────────────────────────────────────

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm test

frontend-lint:
	cd frontend && npm run lint

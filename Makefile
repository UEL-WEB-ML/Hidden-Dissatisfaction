.PHONY: install quality test format db-up db-down db-logs migrate migrate-info p4-release-verify

install:
	python -m pip install -e ".[ml,notebook,dev]"

quality:
	ruff check .
	black --check .
	mypy src tests
	pytest --cov=hidden_dissatisfaction --cov-report=term-missing
	# Domain and application layers must stay fully covered (planning.md 4.4)
	pytest tests/unit tests/contract -q --cov=hidden_dissatisfaction.domain --cov=hidden_dissatisfaction.application --cov-fail-under=100

test:
	pytest

format:
	ruff check --fix .
	black .

db-up:
	docker compose up -d

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

migrate:
	docker compose run --rm migrate

migrate-info:
	docker compose exec postgres psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c 'SELECT version, applied_at FROM app.schema_migrations ORDER BY version'

# Opt-in gate: this requires the complete Olist warehouse and a completed run.
p4-release-verify:
	@test -n "$(DBT_USER)" || (echo "DBT_USER is required for release verification" >&2; exit 1)
	@test -n "$(DBT_PASSWORD)" || (echo "DBT_PASSWORD is required for release verification" >&2; exit 1)
	@test -n "$(DBT_SOURCE_RUN_ID)" || (echo "DBT_SOURCE_RUN_ID is required for release verification" >&2; exit 1)
	uv run --frozen --extra warehouse dbt build --project-dir dbt --profiles-dir dbt --select +gold.ml_modelling_items stg_sellers --exclude tag:release_only --vars "{source_run_id: $(DBT_SOURCE_RUN_ID)}"
	uv run --frozen --extra warehouse dbt test --project-dir dbt --profiles-dir dbt --select tag:release_only --vars "{source_run_id: $(DBT_SOURCE_RUN_ID)}"

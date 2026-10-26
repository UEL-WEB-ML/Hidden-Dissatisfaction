.PHONY: install quality test format bootstrap warehouse train score demo-seed app-up e2e release-check clean-checkout db-up db-down db-logs migrate migrate-info p4-release-verify

COMPOSE ?= docker compose

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
	$(COMPOSE) up -d postgres

bootstrap: db-up migrate

warehouse: bootstrap
	$(COMPOSE) --profile jobs run --rm warehouse

train:
	@test -n "$(TRAIN_COMMAND)" || (echo "TRAIN_COMMAND is required (opt-in)" >&2; exit 1)
	$(TRAIN_COMMAND)

score:
	@test -n "$(SCORE_COMMAND)" || (echo "SCORE_COMMAND is required (opt-in)" >&2; exit 1)
	$(SCORE_COMMAND)

demo-seed:
	DEMO_EVIDENCE_DIR=$${DEMO_EVIDENCE_DIR:-data/evidence} scripts/demo-seed.sh

app-up: bootstrap
	$(COMPOSE) up -d api frontend

e2e: app-up demo-seed
	@test -x tests/smoke.sh && tests/smoke.sh || (echo "tests/smoke.sh is missing or not executable" >&2; exit 1)
	@test -x tests/demo_e2e.sh && tests/demo_e2e.sh
	@$(COMPOSE) ps --status running api frontend | grep -Eq 'api|frontend'

release-check:
	scripts/release-check.sh

clean-checkout:
	scripts/clean-checkout-check.sh

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

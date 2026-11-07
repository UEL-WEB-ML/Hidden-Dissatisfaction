# Local development

Run every command from the repository root.

## One-command application lifecycle

Create and edit the environment file once:

```bash
cp .env.example .env
```

Replace all placeholder passwords and secrets, then use:

```bash
make start  # build, migrate and start PostgreSQL, API and frontend
make stop   # stop the stack and preserve named volumes
```

The default URLs are `http://localhost:4200` for the frontend and
`http://localhost:8000` for the API. `make start` does not seed or replace
business data. Use `make demo-seed` explicitly when a fresh local database needs
the synthetic review fixture.

## Python environment

Python 3.11 and `uv` are required:

```bash
uv python install 3.11
uv sync --frozen --extra db --extra api --extra ml --extra notebook --extra dev
uv run pytest
```

Optional CatBoost support:

```bash
uv sync --frozen --extra ml --extra boosting --extra notebook --extra dev
```

## Resource-aware execution

Use a small, committed fixture for routine local development. Run only the
relevant unit, contract, or sample-data integration tests locally; do not run
full dbt builds, full training, large bootstrap jobs, or SHAP across the whole
dataset on a constrained workstation.

Run milestone jobs that require the complete Olist dataset on the project
server: full warehouse builds, modelling-dataset export, final P5 training and
evaluation, P6 scoring, and Compose/E2E validation. The server clone receives
source code through Git, while raw data, `.env` files, generated Parquet files,
model artifacts, and experiment outputs are transferred or created outside
Git. Store these large files on the Linux filesystem rather than a mounted
Windows drive when working in WSL.

Before a server run, freeze the commit SHA, input manifest, run configuration,
and environment versions. Copy back the resulting manifests, metrics, figures,
and release metadata needed as reproducibility evidence; never commit raw
customer or review data.

## Olist data

Download the nine Olist CSV files into `data/raw/olist/`. The directory is mounted read-only into PostgreSQL at `/data/raw/olist` and is ignored by Git.

```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
```

See [`data-contract.md`](data-contract.md) for required filenames and validation rules.

## PostgreSQL

```bash
cp .env.example .env
# Change POSTGRES_SUPERUSER_PASSWORD, HD_APP_RUNTIME_PASSWORD and HD_JWT_SECRET in .env.
docker compose up -d postgres
make migrate
docker compose ps
```

The bootstrap creates the `app`, `bronze`, `silver`, `gold` and `ml` schemas. Files in `infra/postgres/init/` run only when the volume is first initialized. `make migrate` executes each forward-only SQL file exactly once and records it in `app.schema_migrations`; it is safe to rerun.
It also creates the `app_api` login, which inherits the least-privilege `app_runtime`
role. API processes must use `HD_DATABASE_URL`, never the PostgreSQL superuser.

```bash
docker compose exec postgres psql -U postgres -d hidden_dissatisfaction -c '\dn'
docker compose logs -f postgres
docker compose down
```

Use `docker compose down -v` only when a full local database reset is intended.

## Bronze ingestion

Create a checksum manifest before loading the local, immutable CSV files. The
manifest is ignored by Git and must be regenerated if any source file changes.

```bash
make bronze-manifest
BRONZE_DSN='postgresql://…' make ingest
```

The loader accepts only the nine filenames and exact headers in
`docs/data-contract.md`, takes a transaction-scoped PostgreSQL advisory lock,
and creates a new historical `bronze.ingestion_runs` record for each load.

## Resource-aware dbt runs

The default dbt profile uses one thread so a WSL laptop does not run large
warehouse models concurrently with PostgreSQL. Start with a narrow selection
and only raise `DBT_THREADS` after checking available RAM and swap:

```bash
DBT_THREADS=1 dbt build --select silver --vars '{source_run_id: "<run-id>"}'
```

`intermediate.int_p4_history` and its downstream product-item mart operate on
the full history and should run on the project server or a machine with enough
free memory. Do not combine that job with training, scoring, or Compose UI
builds on a constrained laptop.

## Optional PostgreSQL ingestion integration test

Point `BRONZE_TEST_DSN` at an isolated database that has already received the
migrations, then run the small-fixture integration test. It does not load the
full Olist CSV files:

```bash
BRONZE_TEST_DSN='postgresql://…' uv run pytest tests/integration/test_postgres_bronze_ingestion.py
```

## Quality checks

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

## Safe local cleanup

Use `make clean-cache` to remove only reproducible Python/dbt caches and build
metadata. It deliberately preserves raw data, processed datasets, artifacts,
experiment runs, evidence files, and Docker volumes.

## Current migration state

The checked-in model implementation and historical generated artifact are still order-level. The target product-item contract is documented, but code and notebooks must complete the migration before `data/processed/modelling_items.parquet` or product-item metrics are treated as final evidence.

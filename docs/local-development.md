# Local development

Run every command from the repository root.

## Python environment

Python 3.11 and `uv` are required:

```bash
uv python install 3.11
uv sync --frozen --extra ml --extra notebook --extra dev
uv run pytest
```

Optional CatBoost support:

```bash
uv sync --frozen --extra ml --extra boosting --extra notebook --extra dev
```

## Olist data

Download the nine Olist CSV files into `data/raw/olist/`. The directory is mounted read-only into PostgreSQL at `/data/raw/olist` and is ignored by Git.

```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
```

See [`data-contract.md`](data-contract.md) for required filenames and validation rules.

## PostgreSQL

```bash
cp .env.example .env
# Change POSTGRES_SUPERUSER_PASSWORD in .env.
docker compose up -d
docker compose ps
```

The bootstrap creates the `app`, `bronze`, `silver`, `gold` and `ml` schemas. Files in `infra/postgres/init/` run only when the volume is first initialized.

```bash
docker compose exec postgres psql -U postgres -d hidden_dissatisfaction -c '\dn'
docker compose logs -f postgres
docker compose down
```

Use `docker compose down -v` only when a full local database reset is intended.

## Quality checks

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

## Current migration state

The checked-in model implementation and historical generated artifact are still order-level. The target product-item contract is documented, but code and notebooks must complete the migration before `data/processed/modelling_items.parquet` or product-item metrics are treated as final evidence.

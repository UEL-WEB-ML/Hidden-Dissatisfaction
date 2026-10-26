# Hidden Dissatisfaction

Single-source repository for the Olist hidden-dissatisfaction research, product contracts, ML pipeline, PostgreSQL environment, web artifacts and thesis report.

## Project contract

The system scores product items belonging to Olist orders delivered on time or early. Olist reviews exist only at order level, so every item inherits its containing order's observed review label. An item score represents low-review risk for the order in the context of that item; it does not prove that the item caused dissatisfaction.

- **ML grain:** product item (`product_item_id`).
- **Workflow, split and bootstrap grain:** order (`order_id`).
- **Target:** observed order review score 1–2 among reviewed orders.
- **Prediction time:** immediately after delivery confirmation and before review information is used.
- **Initial order aggregation:** `max-v1`, the maximum item score in the order.
- **Primary metric:** product-item and aggregated order PR-AUC, with order-clustered uncertainty.
- **Decision use:** prioritize an order queue for human review; no automatic customer action or causal claim.

See [`docs/README.md`](docs/README.md) for the authoritative document order.

## Repository layout

```text
.
├── configs/                  # Versioned experiment configuration
├── data/
│   ├── raw/olist/            # Nine local Olist CSV files; ignored by Git
│   ├── interim/              # Validated intermediate data
│   └── processed/            # Split-ready datasets and manifests
├── docs/                     # Research, BRD, FRD, API and data contracts
├── infra/postgres/init/      # PostgreSQL bootstrap SQL
├── notebooks/               # EDA and report-oriented notebooks
├── references/              # Dated research-source snapshots
├── reports/                  # Versioned experiment/report evidence
├── src/hidden_dissatisfaction/
├── tests/
├── web/
│   ├── Wireframe/
│   ├── SoDo/
│   └── BaoCao_LaTeX/
├── compose.yaml
├── .env.example
└── pyproject.toml
```

## Setup

Python 3.11 and [`uv`](https://docs.astral.sh/uv/) are required.

```bash
uv python install 3.11
uv sync --frozen --extra ml --extra notebook --extra dev
uv run pytest
```

Download the Olist dataset once:

```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
```

The nine expected filenames are listed in [`docs/data-contract.md`](docs/data-contract.md).

## PostgreSQL

```bash
cp .env.example .env
# Change POSTGRES_SUPERUSER_PASSWORD.
docker compose up -d
```

Compose uses the repository-local data path and creates the `app`, `bronze`, `silver`, `gold` and `ml` schemas. See [`docs/local-development.md`](docs/local-development.md) for operations and reset warnings.

### P11 delivery workflow

The delivery graph is deliberately opt-in for data work: API startup never
ingests the full dataset. Run `make bootstrap` for PostgreSQL and migrations,
then `make warehouse` when the raw Olist files are present. Training and
scoring are explicit commands (`TRAIN_COMMAND=... make train` and
`SCORE_COMMAND=... make score`). `make app-up` starts API and frontend after
migrations; `make e2e` probes API live/readiness and the frontend shell, and
verifies the containers are running. The smoke stack uses only schema/bootstrap
fixtures and does not load the full Olist dataset. Development ports bind to
localhost only. Evidence files persist in the `evidence_data` volume and are
mounted read-write only by the API container.

## Quality gates

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

Before promoting any modelling dataset or release, the mandatory P4 release
gate must pass against the complete Olist warehouse and a completed Bronze
ingestion run:

```bash
DBT_USER=... DBT_PASSWORD=... DBT_SOURCE_RUN_ID=<completed-run-uuid> \
  make p4-release-verify
```

The target fails if `DBT_USER`, `DBT_PASSWORD`, or `DBT_SOURCE_RUN_ID` is
unavailable, first builds `+gold.ml_modelling_items`, then runs
`dbt test --select tag:release_only` with the same profile and source-run vars. `DBT_HOST`,
`DBT_PORT`, `DBT_DATABASE`, and `DBT_TARGET_SCHEMA` can configure the
warehouse connection. Ordinary CI does not run this gate because it does not
require the full Olist data. GitHub Actions provides the same gate as a
manually dispatched P4 release verification job; configure its required
repository secrets before dispatching it.

## Current implementation status

The existing Python training pipeline and historical generated artifact are still order-level. The product-item contract is now authoritative, but the notebook, schema code, CLI and tests must complete that migration before product-item outputs are considered final results. The checklist is maintained in [`docs/modeling-training-plan.md`](docs/modeling-training-plan.md).

The former `ML_docs` and `Docker_Environment` repositories are retained only as backups. New project changes belong here.

## Release boundary

P12 Gate 0 is documented in [`docs/evidence/P12-gate-0-release-boundary.md`](docs/evidence/P12-gate-0-release-boundary.md). The current scope is demo-only and non-confirmatory; confirmatory claims remain blocked pending the explicit P5 replacement-holdout gate.

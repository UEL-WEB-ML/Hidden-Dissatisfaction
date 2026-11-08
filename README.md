# Hidden Dissatisfaction

Single-source repository for the Olist hidden-dissatisfaction research, product contracts, ML pipeline, PostgreSQL environment, web artifacts and thesis report.

[![quality](https://github.com/UEL-WEB-ML/Hidden-Dissatisfaction/actions/workflows/quality.yml/badge.svg?branch=dev)](https://github.com/UEL-WEB-ML/Hidden-Dissatisfaction/actions/workflows/quality.yml)

> **Current scope:** local/demo decision-support system. Risk scores in the
> bundled demo are deterministic fixtures, not production model inference.

## Quick start

### Prerequisites

- Docker Engine or Docker Desktop with Compose v2.
- GNU Make.
- Git. Python 3.11 and `uv` are needed only for local development and tests.

Create the local configuration once and replace the placeholder secrets:

```bash
cp .env.example .env
make start
```

`make start` starts PostgreSQL, applies forward-only migrations, builds the API
and frontend images, and starts the complete application.

| Service | Default URL |
|---|---|
| Frontend | <http://localhost:4200> |
| API | <http://localhost:8000> |
| API readiness | <http://localhost:8000/health/ready> |

For a fresh database that needs local review accounts and synthetic workflow
fixtures:

```bash
make demo-seed
```

Local demo credentials come from `.env` and the Git-ignored evidence file at
`data/evidence/P12-DEMO-CREDENTIALS.env`.

Stop all services without deleting PostgreSQL or evidence volumes:

```bash
make stop
```

Do not use `docker compose down -v` unless a full local data reset is intended.

## Project contract

The system scores product items belonging to Olist orders delivered on time or early. Olist reviews exist only at order level, so every item inherits its containing order's observed review label. An item score represents low-review risk for the order in the context of that item; it does not prove that the item caused dissatisfaction.

- **ML grain:** product item (`product_item_id`).
- **Workflow, split and bootstrap grain:** order (`order_id`).
- **Target:** observed order review score 1–2 among reviewed orders.
- **Prediction time:** immediately after delivery confirmation and before review information is used.
- **Initial order aggregation:** `max-v1`, the maximum item score in the order.
- **Primary metric:** product-item and aggregated order PR-AUC, with order-clustered uncertainty.
- **Decision use:** prioritize an order queue for human review; no automatic customer action or causal claim.

See [`BA/README.md`](BA/README.md) for the as-built product contract and
[`docs/README.md`](docs/README.md) for research and operational documentation.

## Repository layout

```text
.
├── configs/                  # Versioned experiment configuration
├── data/
│   ├── raw/olist/            # Nine local Olist CSV files; ignored by Git
│   ├── interim/              # Validated intermediate data
│   └── processed/            # Split-ready datasets and manifests
├── BA/                       # As-built BRD, FRD, API, database and traceability
├── dbt/                      # Silver/Gold transformations and data tests
├── docs/                     # Research, architecture and operational documentation
├── frontend/prototype/       # Delivered static frontend
├── infra/                    # API/jobs images and PostgreSQL migrations
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

The delivered static frontend is [`frontend/prototype/`](frontend/prototype/). `web/Wireframe/` is
archived reference material only, not an active application path. Browser E2E coverage is not claimed
by this repository-level documentation.

## Local Python development

Python 3.11 and [`uv`](https://docs.astral.sh/uv/) are required for local tests,
CLI work and notebooks:

```bash
uv python install 3.11
uv sync --frozen --extra db --extra api --extra ml --extra notebook --extra dev
uv run pytest
```

The application startup does not ingest Olist automatically. Download the nine
CSV files only when running warehouse or modeling work:

```bash
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/raw/olist --unzip
```

The nine expected filenames are listed in [`docs/data-contract.md`](docs/data-contract.md).

## Data and ML workflows

The delivery graph is deliberately opt-in for data work: API startup never
ingests the full dataset. Run `make bootstrap`, `make bronze-manifest`, and
`make ingest` first. Use the completed run UUID printed by ingestion when the
raw Olist files are present:

```bash
DBT_SOURCE_RUN_ID=<completed-run-uuid> make warehouse
```

The UUID must identify exactly one `COMPLETE` row in `bronze.ingestion_runs`.
Training and
scoring are explicit commands (`TRAIN_COMMAND=... make train` and
`SCORE_COMMAND=... make score`). `make start` starts API and frontend after
migrations; `make e2e` probes API live/readiness and the frontend shell, and
verifies the containers are running. The smoke stack uses only schema/bootstrap
fixtures and does not load the full Olist dataset. PostgreSQL and API ports bind
to localhost; the frontend is published on `FRONTEND_PORT`. Evidence files
persist in the `evidence_data` volume and are mounted read-write only by the API
container.

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

The operational web workflow, API and PostgreSQL schemas are implemented and
documented in [`BA/`](BA/). Training and release scoring remain explicit offline
batch workflows; there is no online learning, automatic retraining or automatic
model promotion. The local UI dataset may use real Olist order context, but its
demo risk score must not be reported as model inference. Modeling completion is
tracked in [`docs/modeling-training-plan.md`](docs/modeling-training-plan.md).

The former `ML_docs` and `Docker_Environment` repositories are retained only as backups. New project changes belong here.

## Release boundary

P12 Gate 0 is documented in [`docs/evidence/P12-gate-0-release-boundary.md`](docs/evidence/P12-gate-0-release-boundary.md). The current scope is demo-only and non-confirmatory; confirmatory claims remain blocked pending the explicit P5 replacement-holdout gate.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request. Never
commit `.env`, raw Olist CSV files, generated credentials, evidence uploads or
unreviewed experiment artifacts.

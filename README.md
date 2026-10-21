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

## Quality gates

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

## Current implementation status

The existing Python training pipeline and historical generated artifact are still order-level. The product-item contract is now authoritative, but the notebook, schema code, CLI and tests must complete that migration before product-item outputs are considered final results. The checklist is maintained in [`docs/modeling-training-plan.md`](docs/modeling-training-plan.md).

The former `ML_docs` and `Docker_Environment` repositories are retained only as backups. New project changes belong here.

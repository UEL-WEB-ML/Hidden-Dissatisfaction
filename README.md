# Hidden Dissatisfaction

Research codebase for identifying **1–2 star reviews among Olist orders delivered on time or early**. The prediction point is immediately after delivery confirmation and before review creation.

The project supports diagnosis and budgeted case prioritization. It does **not** claim that a voucher, refund, or customer contact causes a better outcome.

## Research scope

- **Population:** delivered orders where `order_delivered_customer_date <= order_estimated_delivery_date`.
- **Primary outcome:** review score 1–2 among orders with an observed review.
- **Secondary outcome:** whether an order receives a review.
- **Validation:** temporal holdout or rolling-origin evaluation; random split is not the primary result.
- **Primary metrics:** PR-AUC, minority recall/precision, Brier score, calibration, and recall/value captured at 5%, 10%, and 20% budgets.
- **Decision baselines:** random, value-only, risk-only, and risk × value.

See [`docs/research-design.md`](docs/research-design.md) for the complete methodological contract.

## Repository layout

```text
.
├── configs/                    # Versioned experiment configuration
├── data/                       # Local-only raw/interim/processed data
├── docs/                       # Architecture, contracts, and research design
├── notebooks/                  # Exploration and report-oriented analyses
├── src/hidden_dissatisfaction/
│   ├── domain/                 # Pure research rules and invariants
│   ├── application/            # Use cases and ports
│   ├── infrastructure/         # Dataset/model/artifact adapters
│   └── interfaces/             # CLI now; API may be added when required
├── tests/                      # Unit, integration, and acceptance tests
├── artifacts/                  # Generated models and predictions (ignored)
├── reports/                    # Versioned tables/figures intended for reports
└── web/Wireframe/              # Existing static product wireframe
```

Dependency direction:

```text
interfaces ──> application ──> domain
                    ^
                    │
              infrastructure
```

The domain does not import pandas, scikit-learn, web frameworks, or storage SDKs.

## Setup

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[ml,notebook,dev]"
```

Place the nine Olist CSV files in `data/raw/olist/`. Raw data is intentionally excluded from Git.

## Quality gates

```bash
ruff check .
black --check .
mypy src tests
pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

Run the initial vertical slice:

```bash
hidden-dissatisfaction assess-order \
  --order-id demo-001 \
  --delivered-at 2018-01-10T10:00:00 \
  --estimated-at 2018-01-12T00:00:00 \
  --review-score 2 \
  --review-created-at 2018-01-11T00:00:00
```

## Development order

Build one end-to-end research slice at a time:

1. define the domain rule and data contract;
2. define the application port/use case;
3. implement the Olist adapter;
4. expose it through CLI/notebook;
5. add unit and integration tests;
6. record experiment configuration and generated evidence.

Read [`AGENTS.md`](AGENTS.md) before adding code.

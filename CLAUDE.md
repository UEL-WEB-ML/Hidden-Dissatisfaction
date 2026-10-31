# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is
Predicts "hidden dissatisfaction" (1–2★ reviews despite on-time delivery) on the Olist dataset, and serves a case-handling app on top of the scores. Python package `hidden_dissatisfaction` (src/), dbt warehouse (dbt/), Angular frontend (frontend/hidden-dissatisfaction-frontend), Postgres (infra/postgres), Docker Compose. The thesis (LaTeX, Vietnamese) is in `Thesis/latex/` on branch `thesis`.

## Commands
- Install: `make install` (or `uv sync`); the CLI is `hidden-dissatisfaction` (`src/hidden_dissatisfaction/interfaces/cli.py`)
- Full gate: `make quality` (ruff, black --check, mypy src tests, pytest with coverage). `domain` and `application` must keep **100% coverage**.
- Single test: `uv run pytest tests/unit/test_x.py::test_name -q`
- Format: `make format`
- Data and app:
  - `make bootstrap` (postgres + migrations)
  - `make bronze-manifest` → `make ingest BRONZE_DSN=...`
  - `make warehouse` (dbt build)
  - `make app-up`, then `make demo-seed`
  - `make e2e`
- Frontend: `npm test` / `npm run lint` / `npm run build` in the frontend dir, or `make frontend-test` (Docker)
- Training and scoring are opt-in only: `make train TRAIN_COMMAND=...`, `make score SCORE_COMMAND=...`
- Release checks:
  - `make release-check`
  - `make p4-release-verify` (needs the full warehouse, DBT_* vars and DBT_SOURCE_RUN_ID)
- Thesis: `cd Thesis/latex && latexmk -pdf main.tex` (biber)

## Architecture
- Clean layers under `src/hidden_dissatisfaction`:
  - `domain` (pure rules: workflow, queue, scoring, parameters)
  - `application` (use cases, `ports.py` interfaces)
  - `infrastructure` (Postgres/joblib/parquet adapters)
  - `api` (FastAPI, JWT auth, role authorization)
  - `interfaces` (CLI)
  - `modeling` (ML pipeline)
  
  Keep domain free of I/O.
- Data flow:
  - Olist CSVs → bronze (ingestion) → dbt silver/intermediate/gold (`gold.ml_modelling_items`) → parquet export → model training → batch scoring.
  - Scores land in the `ml` schema; the app workflow (cases, contacts, evidence, append-only audit) lives in the `app` schema.
  - SQL migrations are in `infra/postgres/migrations`.
- Release gating: the demo uses SYNTHETIC_DEMO data; real-score release requires verification gates.

## Research invariants (from CONTRIBUTING.md)
- Features must be computable at delivery time and fit on training data only. Use strict history cutoffs; no leakage.
- All items of one `order_id` stay in the same temporal split and bootstrap cluster.
- Order scores follow the versioned aggregation rule `max-v1`.
- Report minority-class and calibration metrics (PR-AUC, Brier, Recall@5%).
- Claims are predictive/associational, not causal.
- Never commit raw data, credentials, or large artifacts.

## Docs
`docs/` is partly outdated. `docs/BA_consolidated_as_built.md` reflects the current code. `planning.md` holds the plan, and `SERVER_CONTEXT/` holds experiment evidence from the training server.

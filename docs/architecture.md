# Architecture

## Goal

Keep research rules independent from pandas, model libraries, file formats, notebooks, and future HTTP delivery. This makes leakage rules testable and allows adapters to change without rewriting research policy.

## Layers

| Layer | Owns | Must not own |
|---|---|---|
| Domain | cohort eligibility, label semantics, temporal invariants, domain errors | dataframes, file paths, sklearn estimators, HTTP |
| Application | experiment/use-case orchestration and required ports | CSV parsing, concrete estimators, UI behavior |
| Infrastructure | Olist ingestion, joins, features, estimators, calibration, artifact persistence | research claims or cohort-policy decisions |
| Interfaces | CLI, notebooks, future API request/response mapping | feature formulas, fitting, business/research rules |

## ML swap tests

The architecture is healthy when:

1. CSV can be replaced by Parquet without changing cohort policy.
2. Logistic Regression can be replaced by CatBoost without changing temporal evaluation.
3. Local artifact storage can be replaced by MLflow/S3 without changing training use cases.
4. A CLI can be replaced by an API without moving model logic into the route.
5. Domain tests run without pandas or scikit-learn installed.

## Initial vertical slice

The checked-in slice assesses whether one delivered order belongs to the primary cohort and derives its observed low-review label. It establishes:

- a pure domain entity;
- explicit exclusion reasons;
- an application source port and summary use case;
- a thin CLI boundary;
- unit tests for prediction-time and label invariants.

Olist joins and model training should be added as subsequent tested slices, not as unverified notebook copies.

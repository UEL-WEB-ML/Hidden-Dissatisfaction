# Modeling and training implementation plan

This document is the execution checklist for the first reproducible modeling pipeline. It is
derived from `research-design.md`, `data-contract.md`, and `architecture.md`. The notebook in
`ds_with_ai_capstone` is used only as a presentation reference; its random split, feature choices,
and evaluation logic are not copied.

## Definition of done

The pipeline is complete when a clean checkout can install the `ml` and `dev` extras, consume the
order-grain dataset produced by notebook `02`, train all declared baselines with temporal splits,
select and calibrate a model without touching the final test period, write reproducible artifacts,
and pass unit tests plus the repository quality workflow.

## Decisions fixed before training

- [x] Unit of analysis: one delivered order.
- [x] Prediction time: `order_delivered_customer_date`.
- [x] Population: delivered on or before the estimated date, with an observed review.
- [x] Primary target: `negative`, meaning review score 1 or 2.
- [x] Forbidden model inputs: identifiers, review fields, label-quality fields, and split metadata.
- [x] Primary model-selection metric: average precision (PR-AUC).
- [x] Candidate families: prevalence baseline, Logistic Regression, Random Forest, and histogram
  gradient boosting.
- [x] Imbalance treatment in the first run: class weights; threshold selection is separate.
- [x] Final test data remains untouched until model and calibration method have been selected.
- [x] Seed: 42.
- [ ] Multiple-review policy receives final thesis approval. The current dataset keeps the latest
  answer and exposes uncertainty flags for sensitivity analysis.

## Phase 1 — Input contract and leakage guardrails

- [x] Define the exact numeric, binary, and categorical feature lists in versioned Python code.
- [x] Validate required columns, unique `order_id`, binary target, parseable prediction timestamps,
  and non-empty data.
- [x] Reject review-derived, identifier, split, and unknown columns from the feature matrix.
- [x] Keep feature selection independent from notebook state.
- [ ] Run notebook `02` against local raw Olist files and place its order-grain output at
  `data/processed/modelling_orders.parquet`.
- [ ] Add the processed-data manifest (source hashes, row count, schema, code revision, and cutoff
  policy) when the raw files are available locally.

## Phase 2 — Temporal evaluation design

- [x] Split on delivery/prediction time rather than the purchase-time `split` column created by the
  exploratory notebook.
- [x] Use explicit boundaries from `configs/experiment.toml`; never infer boundaries from test data.
- [x] Assert chronological ordering and require both classes in every partition.
- [x] Divide validation chronologically into a model-selection segment and a calibration segment.
- [x] Report row counts, date ranges, and prevalence for every partition.
- [ ] Revisit fixed boundaries after rebuilding the dataset and inspecting monthly delivery counts;
  any change must be committed as a config change, not hidden in a notebook.

## Phase 3 — Preprocessing and candidate models

- [x] Numeric path: median imputation; scaling for Logistic Regression.
- [x] Categorical path: most-frequent imputation plus unknown-safe one-hot encoding for linear and
  Random Forest models.
- [x] Boosting path: median imputation plus unknown-safe ordinal encoding to keep the matrix dense.
- [x] Fit each transformer only as part of its estimator pipeline on training data.
- [x] Implement the prevalence baseline as a real estimator with `predict_proba`.
- [x] Use deterministic seeds and bounded parallelism.
- [ ] Add optional CatBoost/LightGBM/XGBoost experiments only after the sklearn baseline is stable;
  they are not required to reproduce the first benchmark.
- [ ] Treat SMOTE as a later ablation and recalibrate probabilities if it is introduced.

## Phase 4 — Selection, thresholding, and calibration

- [x] Compare uncalibrated candidates on the earlier validation segment using PR-AUC.
- [x] Select the best non-test candidate.
- [x] Split the later validation segment chronologically again: fit sigmoid/isotonic calibration on
  the first half and compare Brier score on the second half.
- [x] Retain the uncalibrated model when neither calibration method improves held-out Brier score.
- [x] Select a classification threshold on validation only by minority-class F1.
- [x] Record the selected estimator, calibration method, threshold, seed, and config.
- [ ] Add rolling-origin hyperparameter search after the end-to-end baseline is reproducible.

## Phase 5 — Final evaluation and prioritization

- [x] Compute PR-AUC, ROC-AUC, Brier score, minority precision/recall/F1, and prevalence.
- [x] Compute recall@budget and low-review order value captured at 5%, 10%, and 20%.
- [x] Compare risk ranking with deterministic value-only and expected random policies.
- [x] Bootstrap the primary PR-AUC confidence interval with a fixed seed.
- [x] Export row-level test predictions for audit and later error analysis.
- [ ] Produce calibration and precision-recall plots in the reporting notebook after real data exists.
- [ ] Add subgroup error analysis by month, category, seller history/tenure proxy, and geography.
- [ ] Add global and case-level SHAP analysis with explicitly non-causal wording.

## Phase 6 — Reproducibility and interfaces

- [x] Provide a CLI command for a full training run.
- [x] Save the fitted model locally under ignored `artifacts/models/`.
- [x] Save predictions locally under ignored `artifacts/predictions/`.
- [x] Save a lightweight, versionable JSON run report under `reports/experiments/`.
- [x] Add a thin modeling notebook that calls reusable source code instead of reimplementing it.
- [x] Unit-test contracts, temporal splitting, metrics, and an end-to-end synthetic training run.
- [ ] Execute the notebook and commit report-ready figures/tables after the processed dataset is built.

## Run order

1. Execute `notebooks/02_modelling_dataset.ipynb` with the raw data available.
2. Copy or configure its output as `data/processed/modelling_orders.parquet`.
3. Confirm and, if needed, update temporal boundaries in `configs/experiment.toml`.
4. Run `hidden-dissatisfaction train --data data/processed/modelling_orders.parquet`.
5. Review `reports/experiments/latest.json` before opening the test-result notebook.
6. Execute `notebooks/03_modeling_and_training.ipynb` for presentation tables and figures.
7. Mark remaining checklist items only when backed by a reproducible artifact or test.

## Tracking rule

Checkboxes describe repository implementation, not claimed empirical completion. Items requiring
the private/raw Olist files stay unchecked until a real run has produced and validated the stated
artifact. Any scope or leakage-policy change must update this plan and the relevant contract in the
same pull request.

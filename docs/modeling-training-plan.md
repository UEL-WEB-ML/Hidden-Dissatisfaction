# Modeling and training implementation plan

P5 v3 native-categorical tuning is governed by
[ADR-012](adr/ADR-012-p5-native-categorical-tuning.md), which supersedes the GPU
candidate-set decision in [ADR-011](adr/ADR-011-p5-gpu-candidate.md).
This plan is
implementation scope only; empirical completion is recorded only after the relevant
artifact exists. P4 release-gate evidence is a prerequisite for starting P5.
P5 artifacts remain exploratory-only until the explicit replacement-holdout
gate in [`evidence/P12-gate-0-release-boundary.md`](evidence/P12-gate-0-release-boundary.md)
passes.

This document is the execution checklist for the first reproducible modeling pipeline. It is
derived from `research-design.md`, `data-contract.md`, and `architecture.md`. External capstone
repositories are outside this project's evidence base; their feature choices, metrics, and reported
results must not be copied into this pipeline or thesis.

## Definition of done

The pipeline is complete when a clean checkout can install the `ml` and `dev` extras, consume the
product-item dataset produced by notebook `02`, train all declared baselines with order-grouped temporal splits,
select and calibrate a model without touching the final test period, write reproducible artifacts,
and pass unit tests plus the repository quality workflow.

## Decisions fixed before training

- [x] ML unit: one product item; workflow, temporal split, and review label source remain at order level.
- [x] Prediction time: `order_delivered_customer_date`.
- [x] Population: delivered on or before the estimated date, with an observed review.
- [x] Primary target: `negative`, meaning review score 1 or 2.
- [x] Forbidden model inputs: identifiers, review fields, label-quality fields, and split metadata.
- [x] Primary selection order: maximum v1 order-level PR-AUC; item-level PR-AUC is reported and
  used as a diagnostic.
- [x] Fixed v2 candidate set: the retained CPU baselines (prevalence, Logistic Regression,
  Random Forest, histogram gradient boosting) plus one bounded CatBoost GPU candidate.
- [x] Imbalance treatment in the first run: class weights; threshold selection is separate.
- [x] Final test data remains untouched until model and calibration method have been selected.
- [x] Seed: 42.
- [x] Compare item score policies: unweighted item score, `order_weight`, and the order reference
  policy; the selected policy is reported alongside max-v1 order aggregation.
- [x] Interpretation boundary: an item inherits the containing order's review label; item risk is not evidence that the item caused dissatisfaction.
- [ ] Multiple-review policy receives final thesis approval. The current dataset keeps the latest
  answer and exposes uncertainty flags for sensitivity analysis.

## Phase 1 — Input contract and leakage guardrails

- [ ] Migrate the versioned numeric, binary, and categorical feature lists from the current order baseline to product-item grain.
- [ ] Validate required columns, unique `(order_id, order_item_id)`/`product_item_id`, binary inherited target, parseable prediction timestamps, and non-empty data.
- [x] Reject review-derived, identifier, split, and unknown columns from the feature matrix.
- [x] Keep feature selection independent from notebook state.
- [ ] Run notebook `02` against local raw Olist files and place its product-item output at
  `data/processed/modelling_items.parquet`.
- [ ] Add the processed-data manifest (source hashes, row count, schema, code revision, and cutoff
  policy) when the raw files are available locally.

## Phase 2 — Temporal evaluation design

- [ ] Split orders on delivery/prediction time rather than the purchase-time `split` column created by the exploratory notebook, then keep every item from an order in the same partition.
- [x] Use explicit boundaries from `configs/experiment.toml`; never infer boundaries from test data.
- [x] Assert chronological ordering and require both classes in every partition.
- [x] Use five chronological temporal development segments, preserving order clusters, plus one
  sealed final-test segment.
- [x] Report row counts, date ranges, and prevalence for every partition.
- [ ] Report both order and item counts and assert zero `order_id` overlap between partitions.
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
- [x] Keep the v2 candidate set fixed to the retained CPU baselines plus the single CatBoost GPU
  candidate specified in ADR-011.
- [x] Add deterministic multi-item/multi-seller flags and per-item/per-seller ratio features.
- [ ] Add LightGBM/XGBoost only if CatBoost and corrected sklearn baselines justify wider search.
- [ ] Treat SMOTE as a later ablation and recalibrate probabilities if it is introduced.

## Phase 4 — Selection, thresholding, and calibration

- [x] Compare uncalibrated candidates across the five development segments and select by maximum
  v1 order-level PR-AUC.
- [x] Keep calibration fitting and calibration comparison separated: fit on the designated fit
  portion and compare on the independent comparison portion.
- [x] Retain the uncalibrated model when neither calibration method improves held-out Brier score.
- [x] Select thresholds on development data only: high priority is the top 5%; medium priority
  extends through the top 20%.
- [x] Document item calibration wording and the order-priority score ordering explicitly.
- [x] Record the selected estimator, calibration method, threshold, seed, and config.
- [x] Replace single-period model selection with expanding-window rolling-origin comparison.
- [x] Add deterministic bounded rolling-origin search over seven versioned variants; selection is
  max-v1 order PR-AUC, then Brier score, then declared model simplicity. Calibration and threshold
  selection remain downstream and never enter tuning.

## Phase 5 — Final evaluation and prioritization

- [ ] Compute item-level PR-AUC, ROC-AUC, Brier score, minority precision/recall/F1, and prevalence.
- [ ] Aggregate item scores with `max-v1` and compute the same metrics at order level.
- [ ] Compute order-level recall@budget and low-review order value captured at 5%, 10%, and 20%.
- [x] Compare risk ranking with deterministic value-only and expected random policies.
- [ ] Bootstrap confidence intervals with 1,000 order-cluster resamples, never individual item
  rows, using a fixed seed.
- [ ] Lock the selected model, calibration, aggregation, wording, and thresholds once; run the
  sealed final test exactly once after the lock.
- [x] Export row-level test predictions for audit and later error analysis.
- [x] Provide an artifact-only reporting notebook and reusable renderer for calibration and precision-recall plots; execute it only after real sealed artifacts exist.
- [ ] Add subgroup error analysis by month, category, seller history/tenure proxy, and geography.
- [ ] Add global and case-level SHAP analysis with explicitly non-causal wording (only when saved SHAP artifacts exist; the renderer never recomputes explanations).

## Phase 6 — Reproducibility and interfaces

- [x] Provide a CLI command for a full training run.
- [x] Save the fitted model locally under ignored `artifacts/models/`.
- [x] Save predictions locally under ignored `artifacts/predictions/`.
- [x] Save a lightweight, versionable JSON run report under `reports/experiments/`.
- [x] Add a thin modeling notebook that calls reusable source code instead of reimplementing it.
- [x] Unit-test contracts, temporal splitting, metrics, and an end-to-end synthetic training run.
- [ ] Execute the notebook and commit report-ready figures/tables after the processed dataset is built.

## Run order

1. Update and execute `notebooks/02_modelling_dataset.ipynb` with the raw data available.
2. Write its canonical output as `data/processed/modelling_items.parquet`.
3. Confirm and, if needed, update temporal boundaries in `configs/experiment.toml`.
4. Run `hidden-dissatisfaction train --data data/processed/modelling_items.parquet` after the CLI accepts the item-grain contract.
5. Review `reports/experiments/latest.json` before opening the test-result notebook.
6. Execute `notebooks/03_model_evaluation.ipynb` for presentation tables and figures; it reads artifacts only.
7. Mark remaining checklist items only when backed by a reproducible artifact or test.

## Tracking rule

Checkboxes describe repository implementation, not claimed empirical completion. Items requiring
the private/raw Olist files stay unchecked until a real run has produced and validated the stated
artifact. Any scope or leakage-policy change must update this plan and the relevant contract in the
same pull request.

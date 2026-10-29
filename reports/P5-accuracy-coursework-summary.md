# P5 accuracy improvement — coursework summary

Date: 2026-10-29
Evaluation status: **development / exploratory, non-confirmatory**

## Executive result

The accuracy plan completed ten controlled feature and model-selection phases on frozen temporal
development partitions. The retained model is
`order_weight:random_forest-depth8-leaf5-v1`.

| Metric | Initial baseline | Retained model | Change |
|---|---:|---:|---:|
| Rolling order PR-AUC | 0.136326 | **0.146502** | **+0.010176 (+7.46%)** |
| Rolling Brier | 0.201842 | **0.190663** | **-0.011179 (better)** |
| Selection-holdout order PR-AUC | 0.210955 | 0.210761 | -0.000194 |

The primary rolling PR-AUC improved materially over the initial baseline, while the independent
development holdout remained effectively flat. The `0.25` stop target was not reached.

## Phase decisions

| Phase | Strategy | Best/retained evidence | Decision |
|---|---|---:|---|
| S1 | Seller/category target history | best uplift +0.001508 | Reject |
| S2 | Seller operations | +0.004355 rolling PR-AUC | Retain speed/variability |
| S3 | Geography and route | best change -0.002383 | Reject |
| S4 | Order composition | +0.003789 | Retain counts, ratios and HHI |
| S5 | Payment behavior | best uplift +0.000617 | Reject |
| S6 | Product morphology/content | +0.002032, all folds improve | Retain conditionally |
| S7 | Calendar/prior volume | best change -0.000440 | Reject |
| S8 | Data-quality indicators | -0.002426 | Reject |
| S9 | Controlled interactions | -0.000458 | Reject |
| S10 | LOO and bounded GPU tuning | all retained groups necessary | Keep full retained set and Random Forest |

## Final development feature set

- Baseline price, freight, delivery, product and prior-support features.
- Seller operations speed and variability.
- Order composition counts, ratios and seller/category concentration.
- Product morphology and content-completeness indicators.

Leave-one-group-out reduced rolling PR-AUC by `0.004152` without seller operations, `0.005027`
without order composition, and `0.002032` without product features. No package met the compact-set
removal tolerance.

## GPU challenger result

The best bounded GPU candidate was native-categorical CatBoost depth 6 with L2 regularization 8:

- rolling order PR-AUC: `0.145813`;
- selection-holdout order PR-AUC: `0.223873`;
- selection-holdout Brier: `0.179701`;
- selected calibration: sigmoid, development comparison Brier `0.107131`.

Although its single holdout PR-AUC was higher, its primary rolling PR-AUC was `0.000689` below the
retained Random Forest. The protocol therefore does not promote CatBoost or an ensemble.

## Interpretation and limits

PR-AUC, rather than threshold accuracy, is the primary metric because dissatisfaction is the
minority class. Item rows inherit an order-level review label, so item scores are prioritization
signals and do not prove that a specific product caused dissatisfaction. Point-in-time controls
exclude post-review evidence, limiting leakage but also limiting observable product-quality signal.

The repository's P12 gate records that the historical final-test period was previously disclosed.
Consequently, these results must remain development/exploratory. A confirmatory final result
requires a genuinely untouched replacement holdout locked before inspection.

## Reproducible evidence

- Phase reports: `reports/P5-S1-target-history-ablation.md` through
  `reports/P5-S10-feature-selection.md`.
- GPU run: `reports/experiments/p5-s10-gpu-tuning.json`.
- GPU selection record: `artifacts/checkpoints/p5-s10-gpu-tuning-selection.json`.
- Deliberate-stop analysis: `reports/P5-accuracy-failure-analysis.md`.

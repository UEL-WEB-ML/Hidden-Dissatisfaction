# Per-fold model-variant metrics: server inventory

The repository retains complete, like-for-like fold metrics for the final Random Forest development run and the bounded CatBoost challenger. It does **not** retain the full comparison report for prevalence, logistic regression, or HistGradientBoosting; the `p5-development-selection.json` checkpoint only preserves the selected HGB name and no per-fold values. Do not manufacture a five-family comparison table from these incomplete artefacts.

## Retained Random Forest

Source: `reports/experiments/p5-s6-e15-content.json`. Regime: `order_weight`; feature set: final retained seven groups; calibration is selected only after the folds.

| Variant | Fold | Item PR-AUC | Order PR-AUC | Order Brier | Recall at 5% |
|---|---:|---:|---:|---:|---:|
| RF depth 8, leaf 5 | 1 | 0.153753 | 0.142527 | 0.188331 | 0.114078 |
| RF depth 8, leaf 5 | 2 | 0.188261 | 0.150665 | 0.189891 | 0.130864 |
| RF depth 8, leaf 5 | 3 | 0.186038 | 0.146315 | 0.193767 | 0.118734 |

## Bounded CatBoost GPU challengers

Source: `reports/experiments/p5-s10-gpu-tuning.json`. Regime: `order_weight`; same retained feature groups, but a separate bounded challenger experiment.

| Variant | Fold | Item PR-AUC | Order PR-AUC | Order Brier | Recall at 5% |
|---|---:|---:|---:|---:|---:|
| CatBoost native depth 8 | 1 | 0.135977 | 0.127965 | 0.140249 | 0.111650 |
| CatBoost native depth 8 | 2 | 0.164520 | 0.138281 | 0.148153 | 0.138272 |
| CatBoost native depth 8 | 3 | 0.167310 | 0.140792 | 0.152121 | 0.118734 |
| CatBoost native depth 6, L2=8 | 1 | 0.153472 | 0.144209 | 0.164936 | 0.140777 |
| CatBoost native depth 6, L2=8 | 2 | 0.173726 | 0.146016 | 0.166218 | 0.130864 |
| CatBoost native depth 6, L2=8 | 3 | 0.173447 | 0.147213 | 0.173108 | 0.124011 |
| CatBoost native depth 10, L2=8 | 1 | 0.146367 | 0.136263 | 0.125122 | 0.118932 |
| CatBoost native depth 10, L2=8 | 2 | 0.155628 | 0.128533 | 0.130052 | 0.113580 |
| CatBoost native depth 10, L2=8 | 3 | 0.173924 | 0.147431 | 0.137813 | 0.121372 |

## Missing variant evidence

| Family | Per-fold report available? | What remains |
|---|---|---|
| Prevalence | No | Declared in `configs/experiment.toml`; no retained fold metrics. |
| Logistic regression (C=0.1, C=1) | No | Declared in config; no retained fold metrics. |
| Random Forest | Yes, one retained variant | Depth 8/leaf 5 final run above; no retained per-fold depth 12/leaf 10 report. |
| HistGradientBoosting | No | Checkpoint says HGB L2=5/leaf 15 was selected in an earlier protocol, but gives no metrics. |
| CatBoost | Yes, three bounded GPU variants | Values above; they do not replace the retained RF by the primary rolling PR-AUC rule. |

For a single fair all-family Ch.4 table, rerun the declared variants on one frozen feature set and identical rolling folds, then archive the report JSON. The current inventory supports a transparent partial table, not a complete five-family ranking.

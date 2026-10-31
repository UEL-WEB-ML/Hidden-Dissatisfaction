# Chapter 4 evidence and availability status

## 7. Available rolling-fold results

Retained model: `order_weight:random_forest-depth8-leaf5-v1`; calibration: sigmoid. These are development-only results from `reports/experiments/p5-s6-e15-content.json`, not sealed-test results.

| Fold | Item PR-AUC | Order PR-AUC (`max-v1`) | Order Brier | Recall at top 5% orders |
|---|---:|---:|---:|---:|
| 1 | 0.153753 | 0.142527 | 0.188331 | 0.114078 |
| 2 | 0.188261 | 0.150665 | 0.189891 | 0.130864 |
| 3 | 0.186038 | 0.146315 | 0.193767 | 0.118734 |
| Mean | 0.176017 | 0.146502 | 0.190663 | 0.121225 |

Fold-level ROC-AUC is not emitted by this report, and it does not emit item-level Brier. Do not infer either metric from the table.

## 8–11. Sealed-test, prioritization, predictions, and SHAP

| Requested item | Status | Reason |
|---|---|---|
| Sealed-test metrics and bootstrap confidence intervals | Not available | The finalization gate prohibits scoring the historically disclosed test period without a genuinely untouched replacement holdout. |
| 5/10/20% operating results, random and order-value baselines | Not available for test | Thresholds were selected on validation; test budget metrics were not emitted. |
| Row-level test predictions | Not available | No test finalization occurred, so `artifacts/predictions/` has no CSV. |
| SHAP values or plots | Not available | No SHAP run/artifact exists. |

The development policy selects the top 5% of orders as HIGH and the top 20% as MEDIUM-or-higher. An earlier retained Random Forest run recorded `high_from=0.2857879098` and `medium_from=0.1119326946`; the later GPU challenger has different thresholds and is not the retained global winner. These are development thresholds, not sealed-test operating results.

For Chapter 4, report the rolling table as exploratory. Confirmatory test performance, bootstrap CIs, PR/calibration curves, SHAP, and budget comparisons require a newly locked holdout and an authorized finalization run.

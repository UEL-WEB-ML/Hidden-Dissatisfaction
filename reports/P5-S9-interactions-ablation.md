# P5 S9 controlled-interaction ablation decision

Date: 2026-10-29

## Protocol

- Dataset: `p5-item-v11-interactions`, 97,884 items / 85,425 orders.
- Starting retained set: S2 speed/variability, S4 order composition, and S6 morphology/content.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Sealed final test was not scored.

## Result

| Experiment | Added group | Rolling order PR-AUC | Uplift vs retained S6 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| Retained S6 | morphology + content completeness | 0.146502 | — | 0.190663 | 0.210761 | baseline |
| E19 | four hypothesis-led interactions | 0.146044 | -0.000458 | 0.190525 | 0.216289 | reject |

The interaction group lowers mean PR-AUC and declines in folds 1 and 2. Slightly better Brier and
selection-holdout PR-AUC are not enough to retain it under the frozen ranking-first protocol.

## Retained set after S9

`baseline + seller_operations_speed_variability + order_composition_counts + order_composition_ratios + order_composition_concentration + product_morphology + product_content_completeness`

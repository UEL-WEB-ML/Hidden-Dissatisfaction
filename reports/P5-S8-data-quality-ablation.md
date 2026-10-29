# P5 S8 data-quality indicator ablation decision

Date: 2026-10-29

## Protocol

- Dataset: `p5-item-v10-data-quality`, 97,884 items / 85,425 orders.
- Starting retained set: S2 speed/variability, S4 order composition, and S6 morphology/content.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Sealed final test was not scored.

## Result

| Experiment | Added group | Rolling order PR-AUC | Uplift vs retained S6 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| Retained S6 | morphology + content completeness | 0.146502 | — | 0.190663 | 0.210761 | baseline |
| E18 | category/payment/customer/carrier quality flags + missing count | 0.144076 | -0.002426 | 0.193056 | 0.207940 | reject |

The group reduced PR-AUC in every fold except a near-tie in fold 3, worsened Brier, and lowered
selection-holdout PR-AUC. It is not retained. Existing S6 morphology/content indicators remain
retained independently.

## Retained set after S8

`baseline + seller_operations_speed_variability + order_composition_counts + order_composition_ratios + order_composition_concentration + product_morphology + product_content_completeness`

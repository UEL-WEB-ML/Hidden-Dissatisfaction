# P5 S10 feature-selection and leave-one-group-out decision

Date: 2026-10-29

## Protocol

- Dataset: retained development snapshot, 97,884 items / 85,425 orders.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Reference: retained S6 feature set; every LOO run removes exactly one retained package.
- Sealed final test was not scored.

## Leave-one-group-out results

| Run | Removed package | Rolling order PR-AUC | Change vs full | Rolling Brier | Selection holdout PR-AUC |
|---|---|---:|---:|---:|---:|
| Full retained | none | 0.146502 | — | 0.190663 | 0.210761 |
| LOO seller | seller speed + variability | 0.142350 | -0.004152 | 0.195610 | 0.211337 |
| LOO order composition | counts + ratios + HHI | 0.141475 | -0.005027 | 0.190203 | 0.199938 |
| LOO product | morphology + content completeness | 0.144470 | -0.002032 | 0.194563 | 0.218486 |

Every retained package lowers rolling PR-AUC by more than the compact-set tolerance of `0.002`
when removed. The compact feature set is therefore identical to the retained full set:

`baseline + seller_operations_speed_variability + order_composition_counts + order_composition_ratios + order_composition_concentration + product_morphology + product_content_completeness`

## Bounded GPU tuning

GPU access was restored and the three predeclared native-categorical CatBoost variants were run on
the same retained feature set and frozen development partitions.

| Variant | Rolling order PR-AUC | Rolling Brier | Selection AP | Selection holdout order PR-AUC | Selection holdout Brier |
|---|---:|---:|---:|---:|---:|
| CatBoost GPU depth 8 | 0.135679 | 0.146841 | 0.155936 | 0.200429 | 0.167436 |
| CatBoost GPU depth 6, L2 8 | **0.145813** | 0.168087 | **0.166882** | **0.223873** | 0.179701 |
| CatBoost GPU depth 10, L2 8 | 0.137409 | **0.130996** | 0.158640 | 0.198608 | **0.155181** |

Depth 6 is the winner inside the bounded GPU candidate set. It does not replace the retained global
winner: its rolling order PR-AUC is `0.000689` below the Random Forest reference (`0.146502`). The
better single selection-holdout score is secondary evidence and cannot override the frozen primary
rolling metric. Calibration selected sigmoid (development comparison Brier `0.107131`).

The GPU selection artifact is
`artifacts/checkpoints/p5-s10-gpu-tuning-selection.json`; the complete development report is
`reports/experiments/p5-s10-gpu-tuning.json`.

## Decision and scope boundary

- Retain `order_weight:random_forest-depth8-leaf5-v1` as the global development winner.
- Retain the full seven-group feature set; no compact package met the removal tolerance.
- Do not add an ensemble: no second model demonstrated the required stable `0.005` PR-AUC uplift.
- Do not open or rerun the historical final-test partition. P12 requires a genuinely untouched
  replacement holdout before any confirmatory claim.
- Close bounded accuracy tuning as a deliberate stop below the `0.25` development target and move
  any further work to a new-data, target, or research-design decision.

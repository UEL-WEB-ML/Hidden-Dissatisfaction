# P5 S7 calendar and temporal-volume ablation decision

Date: 2026-10-29

## Protocol

- Dataset: `p5-item-v9-temporal-features`, 97,884 items / 85,425 orders.
- Starting retained set: S2 speed/variability, S4 order composition, and S6 morphology/content.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Sealed final test was not scored.

## Data contract

Calendar mappings are deterministic. Volume features use a daily timeline over the wider
delivered-order population; events on the prediction cutoff day are excluded, and no review or
target field is used. dbt row-grain and range invariant tests passed.

## Results

| Experiment | Added group | Rolling order PR-AUC | Uplift vs retained S6 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| Retained S6 | morphology + content completeness | 0.146502 | — | 0.190663 | 0.210761 | baseline |
| E16 | calendar | 0.146062 | -0.000440 | 0.183089 | 0.211722 | reject |
| E17 | E16 + strict prior volume | 0.142799 | -0.003703 | 0.177542 | 0.211943 | reject |

Calendar increased fold 1/2 PR-AUC but reduced fold 3 from `0.146315` to `0.140514`, consistent
with the anticipated era/seasonality overfit risk. Adding prior-volume features further reduced
rolling PR-AUC. Better Brier scores do not override the primary ranking metric; no S7 group is
retained.

## Retained set after S7

`baseline + seller_operations_speed_variability + order_composition_counts + order_composition_ratios + order_composition_concentration + product_morphology + product_content_completeness`

The next strategy should start from this retained set.

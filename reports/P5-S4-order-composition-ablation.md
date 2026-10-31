# P5 S4 order-composition ablation decision

Date: 2026-10-28

## Protocol

- Dataset: `p5-item-v6-order-composition`, 97,884 items / 85,425 orders.
- Starting retained set: `baseline + seller_operations_speed_variability`.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Sealed final test was not scored.

## Data contract

Order totals use `item_plus_freight_amount`; therefore `order_freight_share` is
`freight_total / order_item_value_total`. Null categories are explicitly assigned the
`(missing)` bucket. Counts, shares and HHI are repeated identically at every item in an order.
The S4 dbt model has row-grain, consistency, boundedness and value-share reconciliation tests.

## Results

| Experiment | Incremental groups | Rolling order PR-AUC | Uplift vs retained S2 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| Retained S2 | speed + variability | 0.140681 | — | 0.193378 | 0.207825 | baseline |
| E08 | counts + flags | 0.139932 | -0.000749 | 0.193688 | 0.209869 | reject alone |
| E09 | E08 + value/freight ratios | 0.142751 | +0.002070 | 0.192802 | 0.212091 | continue |
| E10 | E09 + seller/category HHI | 0.144470 | +0.003789 | 0.194563 | 0.218486 | retain conditionally |
| E11 | E10 + distribution statistics | 0.141991 | +0.001310 | 0.192897 | 0.213540 | reject distribution |

E10 improved PR-AUC in every rolling fold (`0.141718`, `0.148118`, `0.143575`) versus
retained S2 (`0.140642`, `0.145510`, `0.135893`), and improved selection-holdout PR-AUC.
Its Brier score is worse by `0.001185`, while recall@5% is mixed; it is retained
conditionally rather than finalized. Counts alone are not retained, but they remain part of the
validated E10 package because the planned sequential ablation showed the ratios and HHI recover
and then improve the ranking signal.

## Retained set after S4

`baseline + seller_operations_speed_variability + order_composition_counts + order_composition_ratios + order_composition_concentration`

Distribution statistics are not retained. The next strategy should start from this retained set.

# P5 S5 payment-behavior ablation decision

Date: 2026-10-28

## Protocol

- Dataset: `p5-item-v7-payment-behavior`, 97,884 items / 85,425 orders.
- Starting retained set: S2 speed/variability plus S4 counts, ratios and HHI.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Sealed final test was not scored.

## Data quality and contract

Payment types are `credit_card` (76,795 rows), `boleto` (19,784), `voucher` (5,775),
`debit_card` (1,529), and `not_defined` (3). There are no null payment types or negative
payment values/installments. The implementation aggregates payments to one row/order before
joining the item cohort; row-grain, invariant, and per-order consistency tests passed.

## Results

| Experiment | Added group | Rolling order PR-AUC | Uplift vs retained S4 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| Retained S4 | counts + ratios + HHI | 0.144470 | — | 0.194563 | 0.218486 | baseline |
| E12 | payment structure | 0.141414 | -0.003056 | 0.193425 | 0.213942 | reject |
| E13 | E12 + type shares/HHI/primary type | 0.145087 | +0.000617 | 0.194200 | 0.212619 | reject |

E13 improves fold 1 only (`0.144538` vs `0.141718`) and declines in folds 2 and 3. Its tiny
mean uplift and lower selection-holdout PR-AUC do not meet the stability gate, despite a slightly
better Brier score. No S5 group is retained.

## Retained set after S5

`baseline + seller_operations_speed_variability + order_composition_counts + order_composition_ratios + order_composition_concentration`

Payment features remain versioned and tested in the dataset contract, but are excluded from the
next experiment's feature-group list.

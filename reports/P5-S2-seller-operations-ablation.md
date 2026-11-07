# P5 S2 seller operational-history ablation decision

Date: 2026-10-28

## Protocol

- Dataset: `p5-item-v4-seller-operations`, 97,884 items / 85,425 orders.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Same frozen rolling-origin boundaries as E00; sealed final test was not scored.
- Operational history uses delivered orders from the wider population, including late deliveries,
  and contains no review fields.

## Results

| Experiment | Added group | Rolling order PR-AUC | Uplift vs E00 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| E00 | none | 0.136326 | — | 0.201842 | 0.210955 | baseline |
| E05 | tenure + volume | 0.132358 | -0.003969 | 0.192903 | 0.195613 | reject |
| S2-A | speed + variability | 0.140681 | +0.004355 | 0.193378 | 0.207825 | retain conditionally |
| S2-B | reliability only | 0.137057 | +0.000730 | 0.200630 | 0.210474 | reject |
| S2-C | trend only | 0.136126 | -0.000200 | 0.194394 | 0.199168 | reject |
| S2-D | retained speed + reliability | 0.137307 | -0.003375 vs S2-A | 0.193768 | 0.207630 | reject reliability |
| S2-E | retained speed + trend | 0.136998 | -0.003683 vs S2-A | 0.189196 | 0.207565 | reject trend |

## Fold evidence for retained group

Speed + variability improved order PR-AUC in all three folds:

| Fold | E00 PR-AUC | Speed PR-AUC | E00 recall@5% | Speed recall@5% |
|---:|---:|---:|---:|---:|
| 1 | 0.130500 | 0.140642 | 0.101942 | 0.104369 |
| 2 | 0.144681 | 0.145510 | 0.118519 | 0.113580 |
| 3 | 0.133798 | 0.135893 | 0.102902 | 0.100264 |

The group passes the conditional gate through `+0.004355` mean PR-AUC, clear Brier improvement,
and positive PR-AUC uplift in every fold. Recall@5% is mixed and remains a caveat; therefore the
group is retained conditionally rather than declared final.

## Retained set after S2

`baseline + seller_operations_speed_variability`

Tenure/volume, reliability, and trend are not retained. The next strategy must start from the
retained speed/variability set, not from the full S2 schema.

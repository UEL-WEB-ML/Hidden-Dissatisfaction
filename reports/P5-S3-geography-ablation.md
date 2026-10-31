# P5 S3 logistics and geography ablation decision

Date: 2026-10-28

## Protocol

- Dataset: `p5-item-v5-geography`, 97,884 items / 85,425 orders.
- Starting retained set: `baseline + seller_operations_speed_variability`.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Sealed final test was not scored.

## Data quality

- Valid seller/customer centroid distance: 97,411 items.
- Missing centroid/distance: 473 items.
- Median distance: 425.14 km; maximum: 3,387.32 km.
- Route-pair cardinality: 404.

## Results

| Experiment | Added group | Rolling order PR-AUC | Uplift vs retained S2 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| Retained S2 | speed + variability | 0.140681 | — | 0.193378 | 0.207825 | retained baseline |
| E07 | distance/state/missing flags | 0.136752 | -0.003929 | 0.193387 | 0.208758 | reject |
| S3 route | route categorical only | 0.138298 | -0.002383 | 0.210551 | 0.212407 | reject |

Distance reduced fold 3 PR-AUC from `0.135893` to `0.127175`. Route categorical reduced it to
`0.124455` and worsened Brier. Neither group passes the retention gate.

Operational route history was not run because its prerequisite geography/route groups failed.
Smoothed route target history was also intentionally skipped because S1 target-history features
were not stable. The retained set remains:

`baseline + seller_operations_speed_variability`

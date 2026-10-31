# P5 S1 target-history ablation decision

Date: 2026-10-28

## Protocol

- Dataset: `p5-item-v3-target-history`, 97,884 items / 85,425 orders.
- Temporal boundaries: unchanged from `configs/experiment.toml`.
- Model/regime held fixed: `order_weight:random_forest-depth8-leaf5-v1`.
- Primary metric: mean rolling-origin order `max-v1` PR-AUC.
- Selection holdout is reported as a stability diagnostic.
- This is a CPU development ablation. The sealed final-test partition was not scored.

## Results

| Experiment | Feature groups | Prior | Rolling order PR-AUC | Uplift vs E00 | Rolling Brier | Selection-holdout PR-AUC |
|---|---|---:|---:|---:|---:|---:|
| E00 | baseline | — | 0.136326 | — | 0.201842 | 0.210955 |
| E01 | baseline + seller | 25 | 0.136052 | -0.000275 | 0.182102 | 0.188170 |
| E02 | baseline + category | 25 | 0.133842 | -0.002484 | 0.181003 | 0.192519 |
| E03 | baseline + seller + category | 25 | 0.134296 | -0.002030 | 0.180223 | 0.185709 |
| E04 | E03 + 30/90-day windows | 25 | 0.135895 | -0.000431 | 0.163963 | 0.159864 |
| S1 seller sensitivity | baseline + seller | 10 | 0.134708 | -0.001618 | 0.184057 | 0.178949 |
| S1 seller sensitivity | baseline + seller | 50 | 0.137834 | +0.001508 | 0.181964 | 0.180534 |
| S1 category sensitivity | baseline + category | 10 | 0.134468 | -0.001859 | 0.182014 | 0.197352 |
| S1 category sensitivity | baseline + category | 50 | 0.132844 | -0.003483 | 0.182369 | 0.195286 |

## Decision

Do not retain an S1 target-history group in the canonical selected feature set yet.

- No experiment reached the required `+0.005` primary uplift.
- Seller prior 50 produced the best rolling result, but `+0.001508` is below even the
  conditional `+0.003` gate and its selection-holdout PR-AUC declined materially.
- Brier improved for all S1 variants, especially the window group, but the primary ranking
  metric and selection-holdout stability did not support retention.
- Seller-category history was not run because its prerequisite seller/category groups failed
  the retention gate.

The implemented v3 columns remain available for diagnostics and future model families, but the
next retained experiment must start from E00 baseline. GPU confirmation remains pending because
GPU access is blocked by the operating system.

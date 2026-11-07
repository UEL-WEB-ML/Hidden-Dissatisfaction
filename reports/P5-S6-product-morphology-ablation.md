# P5 S6 product-morphology and content-completeness ablation decision

Date: 2026-10-29

## Protocol

- Dataset: `p5-item-v8-product-morphology`, 97,884 items / 85,425 orders.
- Starting retained set: S2 speed/variability plus S4 counts, ratios and HHI.
- Fixed model/regime: `order_weight:random_forest-depth8-leaf5-v1`.
- Sealed final test was not scored.

## Data contract

Morphology features derive only from product metadata and current item price/freight. Content
length uses product-name/description metadata, never review text. A physical derivation is null
when its denominator or required dimensions are absent; missing and zero are represented by
separate flags. The model has row-grain and invariant dbt tests.

## Results

| Experiment | Added group | Rolling order PR-AUC | Uplift vs retained S4 | Rolling Brier | Selection holdout PR-AUC | Decision |
|---|---|---:|---:|---:|---:|---|
| Retained S4 | counts + ratios + HHI | 0.144470 | — | 0.194563 | 0.218486 | baseline |
| E14 | morphology/freight ratios | 0.142597 | -0.001873 | 0.190763 | 0.216420 | reject alone |
| E15 | E14 + content completeness/missingness | 0.146502 | +0.002032 | 0.190663 | 0.210761 | retain conditionally |

E15 improves rolling PR-AUC in every fold (`0.142527`, `0.150665`, `0.146315`) versus retained
S4 (`0.141718`, `0.148118`, `0.143575`) and improves Brier by `0.003900`. Its selection-holdout
PR-AUC is lower, so the package is retained conditionally and requires later stability analysis.
Morphology alone is not retained, but remains in the validated E15 package because the planned
sequential ablation shows content completeness reverses its isolated reduction.

## Retained set after S6

`baseline + seller_operations_speed_variability + order_composition_counts + order_composition_ratios + order_composition_concentration + product_morphology + product_content_completeness`

Payment groups remain excluded. The next strategy should start from this retained set.

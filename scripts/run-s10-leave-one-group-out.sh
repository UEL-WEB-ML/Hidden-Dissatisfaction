#!/usr/bin/env bash
set -euo pipefail
data_path="${1:-data/processed/modelling_items.parquet}"
runner=".venv/bin/hidden-dissatisfaction"
mkdir -p reports/experiments artifacts/checkpoints
run_experiment() {
  local name="$1"; shift
  "$runner" train --data "$data_path" --config configs/experiment.toml --cpu-only \
    --candidate-variants random_forest-depth8-leaf5-v1 --regimes order_weight \
    --feature-groups baseline "$@" \
    --selection-record "artifacts/checkpoints/${name}-selection.json" \
    > "reports/experiments/${name}.json"
}
# Full retained set is E15. Each run removes exactly one retained group/package.
run_experiment p5-s10-loo-seller \
  order_composition_counts order_composition_ratios order_composition_concentration \
  product_morphology product_content_completeness
run_experiment p5-s10-loo-order-composition \
  seller_operations_speed_variability product_morphology product_content_completeness
run_experiment p5-s10-loo-product \
  seller_operations_speed_variability order_composition_counts order_composition_ratios order_composition_concentration

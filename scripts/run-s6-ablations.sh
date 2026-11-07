#!/usr/bin/env bash
set -euo pipefail
data_path="${1:-data/processed/modelling_items.parquet}"
runner=".venv/bin/hidden-dissatisfaction"
mkdir -p reports/experiments artifacts/checkpoints
run_experiment() {
  local name="$1"; shift
  "$runner" train --data "$data_path" --config configs/experiment.toml --cpu-only \
    --candidate-variants random_forest-depth8-leaf5-v1 --regimes order_weight \
    --feature-groups baseline seller_operations_speed_variability \
      order_composition_counts order_composition_ratios order_composition_concentration "$@" \
    --selection-record "artifacts/checkpoints/${name}-selection.json" \
    > "reports/experiments/${name}.json"
}
run_experiment p5-s6-e14-morphology product_morphology
run_experiment p5-s6-e15-content product_morphology product_content_completeness

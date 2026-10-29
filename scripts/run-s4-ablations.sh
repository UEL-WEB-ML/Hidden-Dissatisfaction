#!/usr/bin/env bash
set -euo pipefail
data_path="${1:-data/processed/modelling_items.parquet}"
runner=".venv/bin/hidden-dissatisfaction"
mkdir -p reports/experiments artifacts/checkpoints
run_experiment() {
  local name="$1"; shift
  "$runner" train --data "$data_path" --config configs/experiment.toml --cpu-only \
    --candidate-variants random_forest-depth8-leaf5-v1 --regimes order_weight \
    --feature-groups baseline seller_operations_speed_variability "$@" \
    --selection-record "artifacts/checkpoints/${name}-selection.json" \
    > "reports/experiments/${name}.json"
}
run_experiment p5-s4-e08-counts order_composition_counts
run_experiment p5-s4-e09-ratios order_composition_counts order_composition_ratios
run_experiment p5-s4-e10-concentration order_composition_counts order_composition_ratios order_composition_concentration
run_experiment p5-s4-e11-distribution order_composition_counts order_composition_ratios order_composition_concentration order_composition_distribution

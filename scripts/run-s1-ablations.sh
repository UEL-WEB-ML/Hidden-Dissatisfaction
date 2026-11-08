#!/usr/bin/env bash
set -euo pipefail

data_path="${1:-data/processed/modelling_items.parquet}"
report_dir="reports/experiments"
selection_dir="artifacts/checkpoints"
runner=".venv/bin/hidden-dissatisfaction"

mkdir -p "$report_dir" "$selection_dir"

run_experiment() {
  local experiment_id="$1"
  shift
  "$runner" train \
    --data "$data_path" \
    --config configs/experiment.toml \
    --cpu-only \
    --candidate-variants random_forest-depth8-leaf5-v1 \
    --regimes order_weight \
    --feature-groups "$@" \
    --selection-record "$selection_dir/${experiment_id}-selection.json" \
    > "$report_dir/${experiment_id}.json"
}

# Development-only E00-E04 matrix. This script intentionally has no
# --finalize-test path, so the sealed partition cannot be scored accidentally.
run_experiment p5-s1-e00-baseline baseline
run_experiment p5-s1-e01-seller baseline seller_target_history
run_experiment p5-s1-e02-category baseline category_target_history
run_experiment p5-s1-e03-combined \
  baseline seller_target_history category_target_history
run_experiment p5-s1-e04-windows \
  baseline seller_target_history category_target_history target_history_windows

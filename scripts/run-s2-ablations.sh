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
run_experiment p5-s2-e00-baseline
run_experiment p5-s2-e05-tenure-volume seller_operations_tenure_volume
run_experiment p5-s2-speed-variability seller_operations_speed_variability
run_experiment p5-s2-reliability seller_operations_reliability
run_experiment p5-s2-trend seller_operations_trend
run_experiment p5-s2-speed-reliability seller_operations_speed_variability seller_operations_reliability
run_experiment p5-s2-speed-trend seller_operations_speed_variability seller_operations_trend

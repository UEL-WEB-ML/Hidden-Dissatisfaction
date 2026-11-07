#!/usr/bin/env bash
set -euo pipefail
data_path="${1:-data/processed/modelling_items.parquet}"
runner=".venv/bin/hidden-dissatisfaction"
mkdir -p reports/experiments artifacts/checkpoints
"$runner" train --data "$data_path" --config configs/experiment.toml --cpu-only \
  --candidate-variants random_forest-depth8-leaf5-v1 --regimes order_weight \
  --feature-groups baseline seller_operations_speed_variability \
    order_composition_counts order_composition_ratios order_composition_concentration \
    product_morphology product_content_completeness data_quality \
  --selection-record artifacts/checkpoints/p5-s8-e18-data-quality-selection.json \
  > reports/experiments/p5-s8-e18-data-quality.json

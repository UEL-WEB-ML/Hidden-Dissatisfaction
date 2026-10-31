#!/usr/bin/env bash
set -euo pipefail
.venv/bin/hidden-dissatisfaction train --data data/processed/modelling_items.parquet \
  --config configs/experiment.toml --candidate-variants \
    catboost-gpu-native-depth8-v2 catboost-gpu-native-depth6-l2-8-v3 catboost-gpu-native-depth10-l2-8-v3 \
  --regimes order_weight --feature-groups baseline seller_operations_speed_variability \
    order_composition_counts order_composition_ratios order_composition_concentration \
    product_morphology product_content_completeness \
  --selection-record artifacts/checkpoints/p5-s10-gpu-tuning-selection.json \
  > reports/experiments/p5-s10-gpu-tuning.json

# Notebooks

Notebooks are for exploration and communicating results. Reusable cohort, feature, split, model, and evaluation logic belongs in `src/hidden_dissatisfaction` and must be tested.

The canonical raw-data path is `data/raw/olist/`, resolved from the repository root. Some checked-in notebook code and outputs still represent the historical order-level pipeline (`modelling_orders.parquet`). Migrate them deliberately to `data/processed/modelling_items.parquet`; do not relabel old outputs as product-item evidence without rerunning and validating the full notebook.

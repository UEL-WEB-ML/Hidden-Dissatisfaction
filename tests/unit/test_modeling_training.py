from __future__ import annotations

from pathlib import Path

import pandas as pd

from hidden_dissatisfaction.modeling.schema import BINARY_FEATURES, NUMERIC_FEATURES
from hidden_dissatisfaction.modeling.training import TrainingConfig, _regime_frame


def test_baseline_experiment_declares_feature_groups() -> None:
    config = TrainingConfig.from_toml(Path("configs/experiment.toml"))

    assert config.feature_groups == ("baseline",)


def test_order_aggregate_builds_one_deterministic_row_per_order() -> None:
    rows: list[dict[str, object]] = []
    for item, category, price, freight, share in (
        ("item-2", "toys", 30.0, 3.0, 0.75),
        ("item-1", "books", 10.0, 1.0, 0.25),
    ):
        row: dict[str, object] = {
            "product_item_id": item,
            "order_id": "order-1",
            "order_weight": 0.5,
            "prediction_at": pd.Timestamp("2018-01-01"),
            "negative": 1,
            "product_category": category,
            "customer_state": "SP",
        }
        row.update(dict.fromkeys(NUMERIC_FEATURES, 2.0))
        row.update(dict.fromkeys(BINARY_FEATURES, 0))
        row.update({"price": price, "freight_value": freight, "item_value_share": share})
        rows.append(row)

    aggregated = _regime_frame(pd.DataFrame(rows), "order_aggregate")

    assert len(aggregated) == 1
    assert aggregated.loc[0, "product_item_id"] == "order-1::order"
    assert aggregated.loc[0, "price"] == 40.0
    assert aggregated.loc[0, "freight_value"] == 4.0
    assert aggregated.loc[0, "item_value_share"] == 0.75
    assert aggregated.loc[0, "product_category"] == "books|toys"
    assert aggregated.loc[0, "order_weight"] == 1.0

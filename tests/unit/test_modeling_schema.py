from __future__ import annotations

import pandas as pd
import pytest

from hidden_dissatisfaction.modeling.schema import (
    FEATURES,
    ModelingDataError,
    add_derived_features,
    validate_feature_list,
    validate_modeling_table,
)


def test_feature_guard_rejects_review_leakage() -> None:
    with pytest.raises(ModelingDataError, match="Forbidden model inputs"):
        validate_feature_list([*FEATURES, "review_score"])


def test_modeling_table_requires_unique_orders() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["same", "same"],
            "order_delivered_customer_date": ["2018-01-01", "2018-01-02"],
            "negative": [0, 1],
        }
    )
    with pytest.raises(ModelingDataError, match="Missing required columns"):
        validate_modeling_table(frame)


def test_order_structure_features_are_deterministic() -> None:
    frame = pd.DataFrame(
        {
            "n_items": [1.0, 4.0],
            "n_products": [1.0, 2.0],
            "n_sellers": [1.0, 2.0],
            "price": [20.0, 100.0],
            "freight": [5.0, 20.0],
            "weight_g": [500.0, 2000.0],
            "seller_prior_neg_rate": [None, 0.2],
        }
    )
    enriched = add_derived_features(frame)
    assert enriched["is_multi_item"].tolist() == [0, 1]
    assert enriched["is_multi_seller"].tolist() == [0, 1]
    assert enriched["items_per_seller"].tolist() == [1.0, 2.0]
    assert enriched["seller_history_available"].tolist() == [0, 1]

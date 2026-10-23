from __future__ import annotations

import pandas as pd
import pytest

from hidden_dissatisfaction.modeling.schema import (
    FEATURES,
    SCHEMA_VERSION,
    ModelingDataError,
    validate_feature_list,
    validate_modeling_table,
)


def _items(**overrides: object) -> pd.DataFrame:
    row = {
        "product_item_id": "item-1",
        "order_id": "order-1",
        "prediction_at": "2026-01-01",
        "negative": 0,
        "order_weight": 1.0,
        **dict.fromkeys(
            (
                "price",
                "freight_value",
                "payment_count",
                "payment_amount",
                "max_payment_installments",
                "seller_prior_review_count",
                "seller_prior_review_score_avg",
                "category_prior_review_count",
                "category_prior_review_score_avg",
            ),
            1,
        ),
        "seller_history_low_support_flag": 0,
        "category_history_low_support_flag": 0,
        "product_category": "x",
        "customer_state": "SP",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_contract_is_versioned_and_item_grained() -> None:
    assert SCHEMA_VERSION == "p5-item-v1"
    assert validate_modeling_table(_items())["product_item_id"].tolist() == ["item-1"]


def test_csv_timestamps_are_normalized_for_prediction_and_raw_dates() -> None:
    frame = _items(
        prediction_at="2026-01-01T12:00:00Z",
        order_purchase_timestamp="2025-12-24T12:00:00Z",
        order_delivered_customer_date="2026-01-03T12:00:00Z",
    )
    normalized = validate_modeling_table(frame)

    assert pd.api.types.is_datetime64_any_dtype(normalized["prediction_at"])
    assert pd.api.types.is_datetime64_any_dtype(normalized["order_purchase_timestamp"])
    assert pd.api.types.is_datetime64_any_dtype(normalized["order_delivered_customer_date"])


def test_invalid_raw_timestamp_is_rejected() -> None:
    with pytest.raises(ModelingDataError, match="order_purchase_timestamp"):
        validate_modeling_table(_items(order_purchase_timestamp="not-a-timestamp"))


def test_items_require_unique_key_and_order_weights_sum_to_one() -> None:
    frame = pd.concat(
        [_items(), _items(product_item_id="item-2", order_weight=0.5)], ignore_index=True
    )
    with pytest.raises(ModelingDataError, match="sum to one"):
        validate_modeling_table(frame)
    with pytest.raises(ModelingDataError, match="unique"):
        validate_modeling_table(pd.concat([_items(), _items()], ignore_index=True))


def test_order_label_and_prediction_time_must_be_consistent() -> None:
    frame = pd.concat(
        [_items(order_weight=0.5), _items(product_item_id="item-2", negative=1, order_weight=0.5)],
        ignore_index=True,
    )
    with pytest.raises(ModelingDataError, match="consistent"):
        validate_modeling_table(frame)


def test_numeric_features_are_coerced_and_bad_values_rejected() -> None:
    assert validate_modeling_table(_items(price="12.5"))["price"].iloc[0] == 12.5
    with pytest.raises(ModelingDataError, match="price must contain numeric"):
        validate_modeling_table(_items(price="not-a-number"))


def test_nullable_historical_averages_are_accepted() -> None:
    normalized = validate_modeling_table(
        _items(seller_prior_review_score_avg=None, category_prior_review_score_avg=None)
    )
    assert pd.isna(normalized["seller_prior_review_score_avg"].iloc[0])
    assert pd.isna(normalized["category_prior_review_score_avg"].iloc[0])


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

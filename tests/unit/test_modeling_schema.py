from __future__ import annotations

import pandas as pd
import pytest

from hidden_dissatisfaction.modeling.schema import (
    BINARY_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    SCHEMA_VERSION,
    ModelingDataError,
    feature_columns_for_groups,
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
        **dict.fromkeys(NUMERIC_FEATURES, 1),
        **dict.fromkeys(BINARY_FEATURES, 0),
        "product_category": "x",
        "customer_state": "SP",
        "route_pair": "SP->SP",
        "primary_payment_type": "credit_card",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_contract_is_versioned_and_item_grained() -> None:
    assert SCHEMA_VERSION == "p5-item-v11-interactions"
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


def test_target_history_rates_counts_and_flags_are_bounded() -> None:
    with pytest.raises(ModelingDataError, match="seller_smoothed_negative_rate"):
        validate_modeling_table(_items(seller_smoothed_negative_rate=1.01))
    with pytest.raises(ModelingDataError, match="global_prior_order_count"):
        validate_modeling_table(_items(global_prior_order_count=-1))
    with pytest.raises(ModelingDataError, match="seller_negative_history_cold_start_flag"):
        validate_modeling_table(_items(seller_negative_history_cold_start_flag=2))


def test_feature_groups_are_explicit_ordered_and_deduplicated() -> None:
    baseline = feature_columns_for_groups(["baseline"])
    seller = feature_columns_for_groups(["baseline", "seller_target_history"])
    combined = feature_columns_for_groups(
        ["baseline", "seller_target_history", "category_target_history"]
    )

    assert "seller_smoothed_negative_rate" not in baseline[0]
    assert "seller_smoothed_negative_rate" in seller[0]
    assert combined[0].count("global_prior_negative_rate") == 1
    with pytest.raises(ModelingDataError, match="include baseline"):
        feature_columns_for_groups(["seller_target_history"])
    with pytest.raises(ModelingDataError, match="Unknown feature groups"):
        feature_columns_for_groups(["baseline", "future_leakage"])

    operations = feature_columns_for_groups(["baseline", "seller_operations_tenure_volume"])
    assert "seller_operational_prior_order_count" in operations[0]
    assert "seller_operational_cold_start_flag" in operations[1]

    geography = feature_columns_for_groups(["baseline", "geography_distance"])
    route = feature_columns_for_groups(["baseline", "geography_route"])
    assert "seller_customer_distance_km" in geography[0]
    assert "route_pair" not in geography[2]
    assert "route_pair" in route[2]

    composition = feature_columns_for_groups(
        ["baseline", "order_composition_counts", "order_composition_concentration"]
    )
    assert "order_seller_count" in composition[0]
    assert "order_seller_hhi" in composition[0]
    assert "multi_seller_flag" in composition[1]

    payment = feature_columns_for_groups(["baseline", "payment_structure"])
    payment_mix = feature_columns_for_groups(
        ["baseline", "payment_structure", "payment_share_concentration"]
    )
    assert "payment_type_count" in payment[0]
    assert "split_payment_flag" in payment[1]
    assert "primary_payment_type" in payment_mix[2]

    morphology = feature_columns_for_groups(["baseline", "product_morphology"])
    content = feature_columns_for_groups(["baseline", "product_content_completeness"])
    assert "product_density_g_cm3" in morphology[0]
    assert "product_dimensions_missing_flag" in morphology[1]
    assert "product_metadata_missing_count" in content[0]
    assert "product_content_missing_flag" in content[1]

    temporal = feature_columns_for_groups(["baseline", "calendar", "temporal_volume"])
    assert "purchase_month" in temporal[0]
    assert "category_recent_volume_delta" in temporal[0]

    quality = feature_columns_for_groups(["baseline", "data_quality"])
    assert "item_data_quality_missing_count" in quality[0]
    assert "data_quality_carrier_delivery_missing_flag" in quality[1]

    interactions = feature_columns_for_groups(["baseline", "interactions"])
    assert "seller_speed_x_freight_ratio" in interactions[0]
    assert "purchase_delivery_zero_flag" in interactions[1]


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

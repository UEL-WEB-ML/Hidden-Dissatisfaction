"""The versioned P5 product-item modelling contract.

The table is item-grained, while labels, prediction cut-offs, and weights are
order-grained.  Keeping that distinction here prevents accidental re-use of
the old one-row-per-order contract.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

SCHEMA_VERSION = "p5-item-v11-interactions"
MODEL_INPUT_SCHEMA_VERSION = SCHEMA_VERSION

BASELINE_NUMERIC_FEATURES = (
    "price",
    "freight_value",
    "payment_count",
    "payment_amount",
    "max_payment_installments",
    "seller_prior_review_count",
    "seller_prior_review_score_avg",
    "category_prior_review_count",
    "category_prior_review_score_avg",
    "estimated_delivery_buffer_days",
    "purchase_to_delivery_days",
    "carrier_to_delivery_days",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
    "order_item_count",
    "order_item_value_total",
    "item_value_share",
)
GLOBAL_TARGET_HISTORY_FEATURES = (
    "global_prior_order_count",
    "global_prior_negative_rate",
)
SELLER_TARGET_HISTORY_FEATURES = (
    "seller_negative_history_count",
    "seller_negative_history_negative_count",
    "seller_negative_history_support_log1p",
    "seller_smoothed_negative_rate",
    "seller_negative_history_score_mean",
)
CATEGORY_TARGET_HISTORY_FEATURES = (
    "category_negative_history_count",
    "category_negative_history_negative_count",
    "category_negative_history_support_log1p",
    "category_smoothed_negative_rate",
)
TARGET_HISTORY_WINDOW_FEATURES = (
    "global_prior_order_count_30d",
    "global_prior_negative_rate_30d",
    "global_prior_order_count_90d",
    "global_prior_negative_rate_90d",
    "seller_negative_history_count_30d",
    "seller_smoothed_negative_rate_30d",
    "seller_negative_history_score_mean_30d",
    "seller_negative_history_count_90d",
    "seller_smoothed_negative_rate_90d",
    "seller_negative_history_score_mean_90d",
    "category_negative_history_count_30d",
    "category_smoothed_negative_rate_30d",
    "category_negative_history_count_90d",
    "category_smoothed_negative_rate_90d",
)
SELLER_CATEGORY_TARGET_HISTORY_FEATURES = (
    "seller_category_negative_history_count",
    "seller_category_negative_history_support_log1p",
    "seller_category_smoothed_negative_rate",
)
SELLER_OPERATIONS_TENURE_VOLUME_FEATURES = (
    "seller_operational_prior_order_count",
    "seller_operational_prior_item_count",
    "seller_operational_prior_order_count_30d",
    "seller_operational_prior_order_count_90d",
    "seller_operational_volume_velocity_30d",
    "seller_days_since_first_observed_order",
    "seller_days_since_first_delivered_order",
    "seller_days_since_previous_delivery",
)
SELLER_OPERATIONS_SPEED_VARIABILITY_FEATURES = (
    "seller_mean_approval_to_carrier_days",
    "seller_mean_carrier_to_delivery_days",
    "seller_mean_purchase_to_delivery_days",
    "seller_std_purchase_to_delivery_days",
    "seller_delivery_cv",
    "seller_mean_freight_value_ratio",
    "seller_std_freight_value_ratio",
)
SELLER_OPERATIONS_RELIABILITY_FEATURES = (
    "seller_prior_late_shipping_rate",
    "seller_prior_late_delivery_rate",
)
SELLER_OPERATIONS_TREND_FEATURES = (
    "seller_mean_purchase_to_delivery_days_30d",
    "seller_mean_purchase_to_delivery_days_90d",
    "seller_recent_vs_long_delivery_delta",
    "seller_prior_late_delivery_rate_30d",
    "seller_prior_late_delivery_rate_90d",
    "seller_late_delivery_rate_30d_vs_90d",
)
GEOGRAPHY_DISTANCE_FEATURES = ("seller_customer_distance_km",)
ORDER_COMPOSITION_COUNT_FEATURES = (
    "order_seller_count",
    "order_category_count",
    "order_product_count",
    "order_unique_product_count",
)
ORDER_COMPOSITION_RATIO_FEATURES = (
    "order_freight_total",
    "order_freight_share",
    "order_max_item_value_share",
    "order_min_item_value_share",
)
ORDER_COMPOSITION_CONCENTRATION_FEATURES = (
    "order_category_hhi",
    "order_seller_hhi",
)
ORDER_COMPOSITION_DISTRIBUTION_FEATURES = (
    "order_price_mean",
    "order_price_std",
    "order_price_max",
    "order_price_min",
    "order_freight_mean",
    "order_freight_std",
    "order_freight_max",
)
PAYMENT_STRUCTURE_FEATURES = (
    "payment_type_count",
    "payment_installments_mean",
    "installment_amount",
    "payment_to_order_value_ratio",
)
PAYMENT_SHARE_CONCENTRATION_FEATURES = (
    "credit_card_payment_share",
    "voucher_payment_share",
    "payment_type_hhi",
)
PRODUCT_MORPHOLOGY_FEATURES = (
    "product_volume_cm3",
    "product_density_g_cm3",
    "product_max_dimension_cm",
    "product_min_dimension_cm",
    "product_dimension_ratio",
    "freight_to_price_ratio",
    "freight_per_kg",
    "photos_per_100_currency",
)
PRODUCT_CONTENT_COMPLETENESS_FEATURES = (
    "product_name_length",
    "product_description_length",
    "product_metadata_missing_count",
)
CALENDAR_FEATURES = (
    "purchase_month",
    "purchase_weekday",
    "purchase_hour",
    "delivery_month",
    "delivery_weekday",
    "delivery_dataset_age_days",
)
TEMPORAL_VOLUME_FEATURES = (
    "global_order_volume_7d",
    "global_order_volume_30d",
    "seller_recent_order_volume_7d",
    "seller_recent_order_volume_30d",
    "category_recent_order_volume_7d",
    "category_recent_order_volume_30d",
    "category_recent_volume_delta",
)
DATA_QUALITY_FEATURES = ("item_data_quality_missing_count",)
INTERACTION_FEATURES = (
    "order_seller_category_complexity",
    "delivery_buffer_to_duration_ratio",
    "seller_speed_x_freight_ratio",
    "density_x_item_value_share",
)
BASELINE_BINARY_FEATURES = (
    "seller_history_low_support_flag",
    "category_history_low_support_flag",
)
SELLER_TARGET_HISTORY_BINARY_FEATURES = (
    "seller_negative_history_cold_start_flag",
    "seller_negative_history_low_support_flag",
)
CATEGORY_TARGET_HISTORY_BINARY_FEATURES = (
    "category_negative_history_cold_start_flag",
    "category_negative_history_low_support_flag",
)
SELLER_CATEGORY_TARGET_HISTORY_BINARY_FEATURES = (
    "seller_category_negative_history_cold_start_flag",
    "seller_category_negative_history_low_support_flag",
)
SELLER_OPERATIONS_BINARY_FEATURES = ("seller_operational_cold_start_flag",)
GEOGRAPHY_BINARY_FEATURES = (
    "same_state_flag",
    "cross_state_flag",
    "same_city_flag",
    "seller_centroid_missing_flag",
    "customer_centroid_missing_flag",
    "route_distance_missing_flag",
)
ORDER_COMPOSITION_BINARY_FEATURES = (
    "multi_item_flag",
    "multi_seller_flag",
    "multi_category_flag",
)
PAYMENT_BINARY_FEATURES = (
    "split_payment_flag",
    "mixed_payment_type_flag",
    "credit_card_payment_flag",
    "boleto_payment_flag",
    "voucher_payment_flag",
    "debit_card_payment_flag",
    "payment_order_value_zero_flag",
)
PRODUCT_MORPHOLOGY_BINARY_FEATURES = (
    "product_dimensions_missing_flag",
    "product_weight_missing_flag",
    "product_photos_missing_flag",
    "product_price_zero_flag",
    "product_weight_zero_flag",
)
PRODUCT_CONTENT_BINARY_FEATURES = ("product_content_missing_flag",)
DATA_QUALITY_BINARY_FEATURES = (
    "category_missing_flag",
    "payment_missing_flag",
    "customer_state_missing_flag",
    "data_quality_carrier_delivery_missing_flag",
)
INTERACTION_BINARY_FEATURES = ("purchase_delivery_zero_flag",)
SOURCE_NUMERIC_FEATURES = (
    BASELINE_NUMERIC_FEATURES
    + GLOBAL_TARGET_HISTORY_FEATURES
    + SELLER_TARGET_HISTORY_FEATURES
    + CATEGORY_TARGET_HISTORY_FEATURES
    + TARGET_HISTORY_WINDOW_FEATURES
    + SELLER_CATEGORY_TARGET_HISTORY_FEATURES
    + SELLER_OPERATIONS_TENURE_VOLUME_FEATURES
    + SELLER_OPERATIONS_SPEED_VARIABILITY_FEATURES
    + SELLER_OPERATIONS_RELIABILITY_FEATURES
    + SELLER_OPERATIONS_TREND_FEATURES
    + GEOGRAPHY_DISTANCE_FEATURES
    + ORDER_COMPOSITION_COUNT_FEATURES
    + ORDER_COMPOSITION_RATIO_FEATURES
    + ORDER_COMPOSITION_CONCENTRATION_FEATURES
    + ORDER_COMPOSITION_DISTRIBUTION_FEATURES
    + PAYMENT_STRUCTURE_FEATURES
    + PAYMENT_SHARE_CONCENTRATION_FEATURES
    + PRODUCT_MORPHOLOGY_FEATURES
    + PRODUCT_CONTENT_COMPLETENESS_FEATURES
    + CALENDAR_FEATURES
    + TEMPORAL_VOLUME_FEATURES
    + DATA_QUALITY_FEATURES
    + INTERACTION_FEATURES
)
SOURCE_BINARY_FEATURES = (
    BASELINE_BINARY_FEATURES
    + SELLER_TARGET_HISTORY_BINARY_FEATURES
    + CATEGORY_TARGET_HISTORY_BINARY_FEATURES
    + SELLER_CATEGORY_TARGET_HISTORY_BINARY_FEATURES
    + SELLER_OPERATIONS_BINARY_FEATURES
    + GEOGRAPHY_BINARY_FEATURES
    + ORDER_COMPOSITION_BINARY_FEATURES
    + PAYMENT_BINARY_FEATURES
    + PRODUCT_MORPHOLOGY_BINARY_FEATURES
    + PRODUCT_CONTENT_BINARY_FEATURES
    + DATA_QUALITY_BINARY_FEATURES
    + INTERACTION_BINARY_FEATURES
)
NUMERIC_FEATURES = SOURCE_NUMERIC_FEATURES
BINARY_FEATURES = SOURCE_BINARY_FEATURES
BASELINE_CATEGORICAL_FEATURES = ("product_category", "customer_state")
CATEGORICAL_FEATURES = BASELINE_CATEGORICAL_FEATURES + ("route_pair", "primary_payment_type")
FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
SOURCE_FEATURES = SOURCE_NUMERIC_FEATURES + SOURCE_BINARY_FEATURES + CATEGORICAL_FEATURES
MODEL_FEATURES = FEATURES

FEATURE_GROUPS = {
    "baseline": (
        BASELINE_NUMERIC_FEATURES,
        BASELINE_BINARY_FEATURES,
        BASELINE_CATEGORICAL_FEATURES,
    ),
    "seller_target_history": (
        GLOBAL_TARGET_HISTORY_FEATURES + SELLER_TARGET_HISTORY_FEATURES,
        SELLER_TARGET_HISTORY_BINARY_FEATURES,
        (),
    ),
    "category_target_history": (
        GLOBAL_TARGET_HISTORY_FEATURES + CATEGORY_TARGET_HISTORY_FEATURES,
        CATEGORY_TARGET_HISTORY_BINARY_FEATURES,
        (),
    ),
    "target_history_windows": (TARGET_HISTORY_WINDOW_FEATURES, (), ()),
    "seller_category_target_history": (
        SELLER_CATEGORY_TARGET_HISTORY_FEATURES,
        SELLER_CATEGORY_TARGET_HISTORY_BINARY_FEATURES,
        (),
    ),
    "seller_operations_tenure_volume": (
        SELLER_OPERATIONS_TENURE_VOLUME_FEATURES,
        SELLER_OPERATIONS_BINARY_FEATURES,
        (),
    ),
    "seller_operations_speed_variability": (
        SELLER_OPERATIONS_SPEED_VARIABILITY_FEATURES,
        (),
        (),
    ),
    "seller_operations_reliability": (SELLER_OPERATIONS_RELIABILITY_FEATURES, (), ()),
    "seller_operations_trend": (SELLER_OPERATIONS_TREND_FEATURES, (), ()),
    "geography_distance": (GEOGRAPHY_DISTANCE_FEATURES, GEOGRAPHY_BINARY_FEATURES, ()),
    "geography_route": ((), (), ("route_pair",)),
    "order_composition_counts": (
        ORDER_COMPOSITION_COUNT_FEATURES,
        ORDER_COMPOSITION_BINARY_FEATURES,
        (),
    ),
    "order_composition_ratios": (ORDER_COMPOSITION_RATIO_FEATURES, (), ()),
    "order_composition_concentration": (
        ORDER_COMPOSITION_CONCENTRATION_FEATURES,
        (),
        (),
    ),
    "order_composition_distribution": (
        ORDER_COMPOSITION_DISTRIBUTION_FEATURES,
        (),
        (),
    ),
    "payment_structure": (PAYMENT_STRUCTURE_FEATURES, PAYMENT_BINARY_FEATURES[:2], ()),
    "payment_share_concentration": (
        PAYMENT_SHARE_CONCENTRATION_FEATURES,
        PAYMENT_BINARY_FEATURES[2:],
        ("primary_payment_type",),
    ),
    "product_morphology": (
        PRODUCT_MORPHOLOGY_FEATURES,
        PRODUCT_MORPHOLOGY_BINARY_FEATURES,
        (),
    ),
    "product_content_completeness": (
        PRODUCT_CONTENT_COMPLETENESS_FEATURES,
        PRODUCT_CONTENT_BINARY_FEATURES,
        (),
    ),
    "calendar": (CALENDAR_FEATURES, (), ()),
    "temporal_volume": (TEMPORAL_VOLUME_FEATURES, (), ()),
    "data_quality": (DATA_QUALITY_FEATURES, DATA_QUALITY_BINARY_FEATURES, ()),
    "interactions": (INTERACTION_FEATURES, INTERACTION_BINARY_FEATURES, ()),
}

# These columns are retained for splitting/diagnostics and may arrive as
# strings when the modelling table was read from CSV.  Normalize them before
# any feature or duration calculations consume the frame.
RAW_TIMESTAMP_COLUMNS = (
    "order_purchase_timestamp",
    "order_delivered_customer_date",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_estimated_delivery_date",
)

KEY_COLUMNS = (
    "product_item_id",
    "order_id",
    "prediction_at",
)
TARGET = "negative"
VALUE_COLUMN = "price"
WEIGHT_COLUMN = "order_weight"
REQUIRED_COLUMNS = frozenset({*KEY_COLUMNS, TARGET, WEIGHT_COLUMN, *SOURCE_FEATURES})

FORBIDDEN_FEATURES = frozenset(
    {
        *KEY_COLUMNS,
        WEIGHT_COLUMN,
        "split",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
        "label_uncertain",
        "review_conflict",
        "review_id_shared",
        "review_version",
        "feature_schema_version",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_estimated_delivery_date",
        TARGET,
    }
)
DENYLIST = FORBIDDEN_FEATURES


class ModelingDataError(ValueError):
    """Raised when a modeling table violates the declared contract."""


def feature_columns_for_groups(
    groups: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Resolve ordered, deduplicated columns for declared experiment groups."""
    if not groups or "baseline" not in groups:
        raise ModelingDataError("Feature groups must include baseline")
    unknown = sorted(set(groups).difference(FEATURE_GROUPS))
    if unknown:
        raise ModelingDataError(f"Unknown feature groups: {', '.join(unknown)}")

    resolved: list[tuple[str, ...]] = []
    for position in range(3):
        requested = {column for group in groups for column in FEATURE_GROUPS[group][position]}
        master = (NUMERIC_FEATURES, BINARY_FEATURES, CATEGORICAL_FEATURES)[position]
        resolved.append(tuple(column for column in master if column in requested))
    return resolved[0], resolved[1], resolved[2]


def validate_modeling_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize a P5 one-row-per-product-item table."""
    if frame.empty:
        raise ModelingDataError("Modeling table is empty")
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ModelingDataError(f"Missing required columns: {', '.join(missing)}")
    for column in ("product_item_id", "order_id"):
        if frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
            raise ModelingDataError(f"{column} must be non-null and nonempty")
    if frame["product_item_id"].duplicated().any():
        raise ModelingDataError("product_item_id must be unique")

    normalized = frame.copy()
    timestamp_columns = ("prediction_at",) + RAW_TIMESTAMP_COLUMNS
    for column in timestamp_columns:
        if column not in normalized:
            continue
        timestamps = pd.to_datetime(normalized[column], errors="coerce")
        if timestamps.isna().any():
            raise ModelingDataError(f"{column} contains missing/invalid values")
        normalized[column] = timestamps

    target = pd.to_numeric(normalized[TARGET], errors="coerce")
    target_values = set(target.dropna().unique())
    if target.isna().any() or not target_values.issubset({0, 1}):
        raise ModelingDataError("negative must be a non-null binary target")
    normalized[TARGET] = target.astype(int)
    for order, group in normalized.groupby("order_id", dropna=False):
        if group[TARGET].nunique() != 1 or group["prediction_at"].nunique() != 1:
            raise ModelingDataError(
                f"label and prediction_at must be consistent within order {order!r}"
            )
    weights = pd.to_numeric(normalized[WEIGHT_COLUMN], errors="coerce")
    if weights.isna().any() or (~weights.gt(0)).any():
        raise ModelingDataError("order_weight must be positive and numeric")
    normalized[WEIGHT_COLUMN] = weights
    sums = normalized.groupby("order_id")[WEIGHT_COLUMN].sum()
    if not sums.sub(1).abs().le(1e-6).all():
        raise ModelingDataError("order_weight must sum to one within each order")
    for column in NUMERIC_FEATURES:
        if column in normalized:
            values = pd.to_numeric(normalized[column], errors="coerce")
            # Null history values are intentional and are imputed inside folds;
            # only non-null values that cannot be parsed are invalid.
            invalid = normalized[column].notna() & values.isna()
            if invalid.any():
                raise ModelingDataError(f"{column} must contain numeric values or nulls")
            normalized[column] = values
    rate_columns = [
        name
        for name in NUMERIC_FEATURES
        if "negative_rate" in name
        or name in {"seller_prior_late_shipping_rate", "seller_prior_late_delivery_rate"}
        or name.startswith("seller_prior_late_delivery_rate_")
    ]
    for column in rate_columns:
        values = normalized[column]
        missing_is_invalid = "negative_rate" in column and values.isna().any()
        outside_range = (values.notna() & ~values.between(0, 1)).any()
        if missing_is_invalid or outside_range:
            raise ModelingDataError(f"{column} must be between zero and one")
    count_columns = [name for name in NUMERIC_FEATURES if name.endswith("_count")]
    for column in count_columns:
        values = normalized[column]
        if values.isna().any() or (~values.ge(0)).any():
            raise ModelingDataError(f"{column} must be nonnegative")
    for column in BINARY_FEATURES:
        values = pd.to_numeric(normalized[column], errors="coerce")
        if values.isna().any() or not set(values.unique()).issubset({0, 1}):
            raise ModelingDataError(f"{column} must be binary")
        normalized[column] = values.astype(int)
    return normalized


def validate_feature_list(features: Sequence[str]) -> None:
    """Fail if callers attempt to bypass the versioned, leakage-safe schema."""
    duplicates = sorted({name for name in features if features.count(name) > 1})
    if duplicates:
        raise ModelingDataError(f"Duplicate features: {', '.join(duplicates)}")
    forbidden = sorted(set(features).intersection(FORBIDDEN_FEATURES))
    if forbidden:
        raise ModelingDataError(f"Forbidden model inputs: {', '.join(forbidden)}")
    unknown = sorted(set(features).difference(FEATURES))
    if unknown:
        raise ModelingDataError(f"Undeclared model inputs: {', '.join(unknown)}")


def validate_runtime_model_input(frame: pd.DataFrame, feature_names: Sequence[str]) -> pd.DataFrame:
    """Validate only the feature payload presented to a released model."""
    validate_feature_list(feature_names)
    if list(feature_names) != list(FEATURES):
        raise ModelingDataError("Runtime model input feature order does not match the schema")
    missing = [name for name in feature_names if name not in frame.columns]
    if missing:
        raise ModelingDataError(f"Missing runtime model inputs: {', '.join(missing)}")
    return frame.loc[:, list(feature_names)].copy()

"""The versioned P5 product-item modelling contract.

The table is item-grained, while labels, prediction cut-offs, and weights are
order-grained.  Keeping that distinction here prevents accidental re-use of
the old one-row-per-order contract.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

SCHEMA_VERSION = "p5-item-v1"

SOURCE_NUMERIC_FEATURES = (
    "price",
    "freight_value",
    "payment_count",
    "payment_amount",
    "max_payment_installments",
    "seller_prior_review_count",
    "seller_prior_review_score_avg",
    "category_prior_review_count",
    "category_prior_review_score_avg",
)
SOURCE_BINARY_FEATURES = (
    "seller_history_low_support_flag",
    "category_history_low_support_flag",
)
NUMERIC_FEATURES = SOURCE_NUMERIC_FEATURES
BINARY_FEATURES = SOURCE_BINARY_FEATURES
CATEGORICAL_FEATURES = ("product_category", "customer_state")
FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
SOURCE_FEATURES = SOURCE_NUMERIC_FEATURES + SOURCE_BINARY_FEATURES + CATEGORICAL_FEATURES

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

"""Versioned feature schema and input validation for the primary model."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

NUMERIC_FEATURES = (
    "delivery_days",
    "days_vs_estimate",
    "promised_days",
    "handoff_days",
    "carrier_to_customer_days",
    "approval_hours",
    "n_items",
    "n_products",
    "n_sellers",
    "price",
    "freight",
    "freight_ratio",
    "distance_km",
    "installments",
    "n_pay",
    "photos",
    "desc_len",
    "weight_g",
    "seller_prior_neg_rate",
    "seller_prior_n",
)
BINARY_FEATURES = ("dispatch_late",)
CATEGORICAL_FEATURES = ("category", "customer_state", "payment_type")
FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES

KEY_COLUMNS = (
    "order_id",
    "customer_unique_id",
    "main_seller",
    "order_purchase_timestamp",
    "order_delivered_customer_date",
)
TARGET = "negative"
VALUE_COLUMN = "price"

FORBIDDEN_FEATURES = frozenset(
    {
        *KEY_COLUMNS,
        "split",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
        "label_uncertain",
        "review_conflict",
        "review_id_shared",
        TARGET,
    }
)
REQUIRED_COLUMNS = frozenset({*KEY_COLUMNS, *FEATURES, TARGET})


class ModelingDataError(ValueError):
    """Raised when a modeling table violates the declared contract."""


def validate_modeling_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize a one-row-per-order modeling table."""
    if frame.empty:
        raise ModelingDataError("Modeling table is empty")
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ModelingDataError(f"Missing required columns: {', '.join(missing)}")
    if frame["order_id"].isna().any() or not frame["order_id"].is_unique:
        raise ModelingDataError("order_id must be non-null and unique")

    normalized = frame.copy()
    timestamps = pd.to_datetime(normalized["order_delivered_customer_date"], errors="coerce")
    if timestamps.isna().any():
        raise ModelingDataError("order_delivered_customer_date contains missing/invalid values")
    normalized["order_delivered_customer_date"] = timestamps

    target_values = set(normalized[TARGET].dropna().astype(int).unique())
    if normalized[TARGET].isna().any() or not target_values.issubset({0, 1}):
        raise ModelingDataError("negative must be a non-null binary target")
    normalized[TARGET] = normalized[TARGET].astype(int)
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

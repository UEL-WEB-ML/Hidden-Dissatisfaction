"""Versioned feature schema and input validation for the primary model."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

SOURCE_NUMERIC_FEATURES = (
    "delivery_days",
    "days_vs_estimate",
    "promised_days",
    "handoff_days",
    "carrier_to_customer_days",
    "approval_hours",
    "n_items",
    "n_products",
    "n_sellers",
    "n_categories",
    "n_seller_states",
    "price",
    "price_max",
    "price_std",
    "freight",
    "freight_max",
    "freight_std",
    "freight_ratio",
    "distance_km",
    "installments",
    "n_pay",
    "photos",
    "desc_len",
    "weight_g",
    "weight_max_g",
    "weight_std_g",
    "seller_prior_neg_rate",
    "seller_prior_n",
)
DERIVED_NUMERIC_FEATURES = (
    "items_per_seller",
    "products_per_seller",
    "price_per_item",
    "freight_per_item",
    "weight_per_item",
)
SOURCE_BINARY_FEATURES = ("dispatch_late",)
DERIVED_BINARY_FEATURES = (
    "is_multi_item",
    "is_multi_product",
    "is_multi_seller",
    "seller_history_available",
)
NUMERIC_FEATURES = SOURCE_NUMERIC_FEATURES + DERIVED_NUMERIC_FEATURES
BINARY_FEATURES = SOURCE_BINARY_FEATURES + DERIVED_BINARY_FEATURES
CATEGORICAL_FEATURES = ("category", "customer_state", "payment_type")
FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
SOURCE_FEATURES = SOURCE_NUMERIC_FEATURES + SOURCE_BINARY_FEATURES + CATEGORICAL_FEATURES

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
REQUIRED_COLUMNS = frozenset({*KEY_COLUMNS, *SOURCE_FEATURES, TARGET})


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
    return add_derived_features(normalized)


def add_derived_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic, prediction-time-safe order structure features."""
    enriched = frame.copy()
    enriched["is_multi_item"] = enriched["n_items"].gt(1).astype(int)
    enriched["is_multi_product"] = enriched["n_products"].gt(1).astype(int)
    enriched["is_multi_seller"] = enriched["n_sellers"].gt(1).astype(int)
    enriched["seller_history_available"] = enriched["seller_prior_neg_rate"].notna().astype(int)
    enriched["items_per_seller"] = _safe_ratio(enriched["n_items"], enriched["n_sellers"])
    enriched["products_per_seller"] = _safe_ratio(enriched["n_products"], enriched["n_sellers"])
    enriched["price_per_item"] = _safe_ratio(enriched["price"], enriched["n_items"])
    enriched["freight_per_item"] = _safe_ratio(enriched["freight"], enriched["n_items"])
    enriched["weight_per_item"] = _safe_ratio(enriched["weight_g"], enriched["n_items"])
    return enriched


def _safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    ratio = numerator.div(denominator.where(denominator.gt(0)))
    return ratio.replace([float("inf"), float("-inf")], pd.NA)


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

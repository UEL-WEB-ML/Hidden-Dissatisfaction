"""Application contract for exporting the modelling item dataset."""

import math
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol


class ItemRecord(Protocol):
    def __getitem__(self, key: str) -> Any: ...


class GoldModellingItemsReader(Protocol):
    """Port for the Gold modelling-items relation/query result."""

    def read_modelling_items(self) -> Iterable[Mapping[str, Any]]: ...


@dataclass(frozen=True)
class ModellingExportMetadata:
    source_run_id: str
    source_hashes: Mapping[str, str]
    cutoff_version: str
    review_policy_version: str
    feature_schema_version: str
    git_sha: str | None = None


@dataclass(frozen=True)
class ModellingExportContract:
    item_key: str = "product_item_id"
    order_key: str = "order_id"
    order_item_key: str = "order_item_id"
    prediction_field: str = "prediction_at"
    label_field: str = "negative"
    weight_field: str = "order_weight"


class InvalidModellingItems(ValueError):
    """Raised when records cannot safely form a modelling dataset."""


def normalize_parquet_scalar(value: Any) -> Any:
    """Convert database scalars unsupported by Arrow without changing feature types."""
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, dict):
        return {key: normalize_parquet_scalar(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_parquet_scalar(item) for item in value]
    if isinstance(value, tuple):
        return tuple(normalize_parquet_scalar(item) for item in value)
    return value


def normalize_item_records(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Normalize only known Arrow-incompatible database scalar values."""
    return [
        {key: normalize_parquet_scalar(value) for key, value in record.items()}
        for record in records
    ]


def validate_item_records(
    records: Iterable[Mapping[str, Any]], contract: ModellingExportContract
) -> list[dict[str, Any]]:
    """Materialise and validate keys and repeated order-level fields."""
    result = [dict(record) for record in records]
    if not result:
        raise InvalidModellingItems("item record stream is empty")
    keys = [row.get(contract.item_key) for row in result]
    if any(key is None or (isinstance(key, str) and not key.strip()) for key in keys):
        raise InvalidModellingItems("item keys must be nonempty")
    if len(set(keys)) != len(keys):
        raise InvalidModellingItems("item keys must be unique")
    required = (
        contract.order_key,
        contract.order_item_key,
        contract.prediction_field,
        contract.label_field,
        contract.weight_field,
    )
    weights: dict[Any, list[float]] = {}
    for row in result:
        missing = [name for name in required if name not in row]
        if missing:
            raise InvalidModellingItems(f"missing required fields: {', '.join(missing)}")
    grouped: dict[Any, tuple[Any, Any]] = {}
    for row in result:
        order = row[contract.order_key]
        order_item = row[contract.order_item_key]
        if order is None or (isinstance(order, str) and not order.strip()):
            raise InvalidModellingItems("order keys must be nonempty")
        if order_item is None or (isinstance(order_item, str) and not order_item.strip()):
            raise InvalidModellingItems("order item keys must be nonempty")
        expected_key = f"{order}-{order_item}"
        if row[contract.item_key] != expected_key:
            raise InvalidModellingItems("product_item_id must equal order_id-order_item_id")
        prediction = row[contract.prediction_field]
        if prediction is None or (isinstance(prediction, str) and not prediction.strip()):
            raise InvalidModellingItems("prediction_at values must be nonempty")
        if row[contract.label_field] is None:
            raise InvalidModellingItems("negative values must be non-null")
        try:
            weight = float(row[contract.weight_field])
        except (TypeError, ValueError):
            raise InvalidModellingItems("order weights must be numeric") from None
        if not math.isfinite(weight) or weight <= 0:
            raise InvalidModellingItems("order weights must be positive and finite")
        weights.setdefault(order, []).append(weight)
        values = (prediction, row[contract.label_field])
        if order in grouped and grouped[order] != values:
            raise InvalidModellingItems(f"inconsistent order-level fields for order {order!r}")
        grouped[order] = values
    for order, order_weights in weights.items():
        if not math.isclose(sum(order_weights), 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise InvalidModellingItems(f"order weights must sum to one for order {order!r}")
    return result

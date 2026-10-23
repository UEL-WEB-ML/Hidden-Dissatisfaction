"""Leakage-safe, order-grouped temporal partitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from hidden_dissatisfaction.modeling.schema import TARGET, ModelingDataError


@dataclass(frozen=True)
class TemporalPartitions:
    train: pd.DataFrame
    selection: pd.DataFrame
    calibration_fit: pd.DataFrame
    calibration_compare: pd.DataFrame
    threshold: pd.DataFrame
    test: pd.DataFrame

    @property
    def calibration(self) -> pd.DataFrame:  # compatibility with the training module
        return pd.concat([self.calibration_fit, self.calibration_compare])

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {
            name: getattr(self, name)
            for name in (
                "train",
                "selection",
                "calibration_fit",
                "calibration_compare",
                "threshold",
                "test",
            )
        }


def _orders(frame: pd.DataFrame, time_column: str) -> pd.DataFrame:
    required = {"order_id", time_column, TARGET}
    missing = required.difference(frame.columns)
    if missing:
        raise ModelingDataError(f"Missing required columns: {', '.join(sorted(missing))}")
    if frame["order_id"].isna().any() or frame[time_column].isna().any():
        raise ModelingDataError("order_id and prediction_at must be non-null")
    grouped = frame.groupby("order_id", sort=False, dropna=False)
    bad = grouped[TARGET].nunique().gt(1) | grouped[time_column].nunique().gt(1)
    if bad.any():
        raise ModelingDataError("order_id has inconsistent prediction_at or negative values")
    return grouped[[time_column, TARGET]].first().reset_index()


def grouped_temporal_split(
    frame: pd.DataFrame,
    *,
    boundaries: Mapping[str, datetime],
    time_column: str = "prediction_at",
) -> TemporalPartitions:
    """Assign every item by its whole order to explicitly bounded cohorts.

    ``boundaries`` must contain increasing ends for train, selection,
    calibration_fit, calibration_compare, threshold, and test.  Intervals are
    left-closed/right-open, so equal timestamps can never be split.
    """
    names = ("train", "selection", "calibration_fit", "calibration_compare", "threshold", "test")
    if tuple(boundaries) != names or any(
        boundaries[n] >= boundaries[names[i + 1]] for i, n in enumerate(names[:-1])
    ):
        raise ModelingDataError("boundaries must be ordered train through test")
    order_table = _orders(frame, time_column)
    assigned = pd.Series(pd.NA, index=order_table.index, dtype="object")
    start = pd.Timestamp.min
    for name in names:
        end = pd.Timestamp(boundaries[name])
        mask = (
            assigned.isna() & order_table[time_column].ge(start) & order_table[time_column].lt(end)
        )
        assigned.loc[mask] = name
        start = end
    if assigned.isna().any():
        raise ModelingDataError("eligible orders fall outside the declared boundaries")
    order_table["split"] = assigned.values
    result = frame.merge(
        order_table[["order_id", "split"]], on="order_id", how="left", validate="many_to_one"
    )
    if result["split"].isna().any():
        raise ModelingDataError("items could not be assigned to an order split")
    parts = TemporalPartitions(
        *(result.loc[result.split.eq(name)].drop(columns="split").copy() for name in names)
    )
    _validate_partitions(parts, time_column)
    return parts


def temporal_split(
    frame: pd.DataFrame,
    *,
    validation_start: datetime,
    test_start: datetime,
    test_end: datetime,
    time_column: str = "order_delivered_customer_date",
) -> TemporalPartitions:
    """Legacy two-validation split, retained for the existing training API."""
    _orders(frame, time_column)  # Validate order-level consistency before splitting.
    validation = frame.loc[
        frame[time_column].ge(validation_start) & frame[time_column].lt(test_start)
    ].sort_values(time_column)
    if validation.empty:
        raise ModelingDataError("Validation period is empty")
    mid = len(validation) // 2
    train = frame.loc[frame[time_column] < validation_start].copy()
    selection, calibration = validation.iloc[:mid].copy(), validation.iloc[mid:].copy()
    test = frame.loc[frame[time_column].ge(test_start) & frame[time_column].lt(test_end)].copy()
    return TemporalPartitions(
        train, selection, calibration, calibration.copy(), calibration.copy(), test
    )


def _validate_partitions(parts: TemporalPartitions, time_column: str) -> None:
    seen: set[object] = set()
    for name, part in parts.as_dict().items():
        if part.empty or part[TARGET].nunique() != 2:
            raise ModelingDataError(f"Temporal partition '{name}' must be non-empty and two-class")
        overlap = seen.intersection(part.order_id)
        if overlap:
            raise ModelingDataError("orders overlap temporal partitions")
        seen.update(part.order_id)


def partition_summary(
    partitions: TemporalPartitions, time_column: str = "prediction_at"
) -> dict[str, dict[str, object]]:
    return {
        n: {
            "item_count": len(p),
            "order_count": p.order_id.nunique(),
            "start": p[time_column].min().isoformat(),
            "end": p[time_column].max().isoformat(),
            "prevalence": float(p[TARGET].mean()),
            "two_class": p[TARGET].nunique() == 2,
        }
        for n, p in partitions.as_dict().items()
    }


def rolling_origin_splits(
    frame: pd.DataFrame,
    *,
    n_splits: int,
    time_column: str = "prediction_at",
    initial_train_fraction: float = 0.4,
) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
    if n_splits < 2 or not 0 < initial_train_fraction < 1:
        raise ModelingDataError("invalid rolling-origin configuration")
    if time_column not in frame and "order_delivered_customer_date" in frame:
        time_column = "order_delivered_customer_date"
    if "order_id" not in frame:
        frame = frame.copy()
        frame["order_id"] = range(len(frame))
    orders = _orders(frame, time_column).sort_values(time_column).reset_index(drop=True)
    initial = int(len(orders) * initial_train_fraction)
    size = (len(orders) - initial) // n_splits
    if initial == 0 or size == 0:
        raise ModelingDataError("not enough orders for rolling-origin validation")
    out = []
    for i in range(n_splits):
        lo, hi = initial + i * size, (
            len(orders) if i == n_splits - 1 else initial + (i + 1) * size
        )
        train_ids, valid_ids = set(orders.iloc[:lo].order_id), set(orders.iloc[lo:hi].order_id)
        train, valid = (
            frame[frame.order_id.isin(train_ids)].copy(),
            frame[frame.order_id.isin(valid_ids)].copy(),
        )
        if train[TARGET].nunique() != 2 or valid[TARGET].nunique() != 2:
            raise ModelingDataError(f"rolling fold {i + 1} must contain both target classes")
        out.append((train, valid))
    return out

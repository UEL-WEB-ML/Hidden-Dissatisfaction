"""Explicit temporal splitting at the delivery-time prediction point."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from hidden_dissatisfaction.modeling.schema import TARGET, ModelingDataError


@dataclass(frozen=True)
class TemporalPartitions:
    """Train, model-selection, calibration, and final-test partitions."""

    train: pd.DataFrame
    selection: pd.DataFrame
    calibration: pd.DataFrame
    test: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        """Return partitions in chronological order."""
        return {
            "train": self.train,
            "selection": self.selection,
            "calibration": self.calibration,
            "test": self.test,
        }


def temporal_split(
    frame: pd.DataFrame,
    *,
    validation_start: datetime,
    test_start: datetime,
    test_end: datetime,
    time_column: str = "order_delivered_customer_date",
) -> TemporalPartitions:
    """Split by explicit delivery-time boundaries and divide validation in time order."""
    if not validation_start < test_start < test_end:
        raise ModelingDataError("Expected validation_start < test_start < test_end")
    time = frame[time_column]
    train = frame.loc[time < validation_start].copy()
    validation = frame.loc[(time >= validation_start) & (time < test_start)].copy()
    test = frame.loc[(time >= test_start) & (time < test_end)].copy()
    if validation.empty:
        raise ModelingDataError("Validation period is empty")

    validation = validation.sort_values(time_column)
    midpoint = len(validation) // 2
    selection = validation.iloc[:midpoint].copy()
    calibration = validation.iloc[midpoint:].copy()
    partitions = TemporalPartitions(train, selection, calibration, test)
    _validate_partitions(partitions, time_column)
    return partitions


def _validate_partitions(partitions: TemporalPartitions, time_column: str) -> None:
    previous_max: pd.Timestamp | None = None
    for name, part in partitions.as_dict().items():
        if part.empty:
            raise ModelingDataError(f"Temporal partition '{name}' is empty")
        if part[TARGET].nunique() != 2:
            raise ModelingDataError(f"Temporal partition '{name}' must contain both target classes")
        current_min = part[time_column].min()
        current_max = part[time_column].max()
        if previous_max is not None and previous_max > current_min:
            raise ModelingDataError(f"Temporal partition '{name}' overlaps its predecessor")
        previous_max = current_max


def partition_summary(
    partitions: TemporalPartitions, time_column: str = "order_delivered_customer_date"
) -> dict[str, dict[str, object]]:
    """Build JSON-safe cohort evidence for every temporal partition."""
    return {
        name: {
            "rows": int(len(part)),
            "start": part[time_column].min().isoformat(),
            "end": part[time_column].max().isoformat(),
            "prevalence": float(part[TARGET].mean()),
        }
        for name, part in partitions.as_dict().items()
    }

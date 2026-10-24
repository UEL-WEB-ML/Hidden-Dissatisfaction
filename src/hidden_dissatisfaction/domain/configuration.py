"""Immutable configuration values used by application decisions."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EffectiveParameterBundle:
    revision: int
    as_of: datetime
    values: dict[str, str]

    def value(self, key: str) -> str:
        return self.values[key]


@dataclass(frozen=True)
class WorkloadCapacity:
    user_id: str
    workload: int
    capacity: int


@dataclass(frozen=True)
class MLThresholds:
    model_release_id: str
    threshold_version: str
    medium: float
    high: float

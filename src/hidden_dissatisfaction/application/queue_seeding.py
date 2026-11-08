"""Seed review cases from an explicitly selected active prediction run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SeededOrder:
    order_id: str
    prediction_id: str
    score: float
    risk_level: str
    aggregation_rule: str = "max-v1"


@dataclass(frozen=True)
class SeedSummary:
    created: int
    skipped: int


class QueueSeedPort(Protocol):
    def seed(self, prediction_id: str, now: datetime) -> SeedSummary: ...


class QueueSeeder:
    def __init__(self, store: QueueSeedPort) -> None:
        self.store = store

    def seed(self, prediction_id: str, now: datetime | None = None) -> SeedSummary:
        if not prediction_id:
            raise ValueError("prediction_id is required")
        return self.store.seed(prediction_id, now or datetime.utcnow())

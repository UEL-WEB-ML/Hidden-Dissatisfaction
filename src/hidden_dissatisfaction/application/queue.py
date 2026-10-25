"""Read port and DTOs for the order-grain Risk Queue."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from hidden_dissatisfaction.domain.queue import QueueFilters


@dataclass(frozen=True)
class QueueOrder:
    order_id: str
    score: float
    level: str
    status: str
    assignee_id: str | None
    assignee_name: str | None
    queued_at: datetime
    sla_due_at: datetime | None
    row_version: int
    matched_item_id: str | None = None


@dataclass(frozen=True)
class QueuePage:
    items: tuple[QueueOrder, ...]
    total: int


class RiskOrderQueryPort(Protocol):
    """Read-only, stable Queue projection at one row per order."""

    def list_orders(self, filters: QueueFilters) -> QueuePage: ...

    def filter_options(self) -> dict[str, tuple[str, ...]]: ...

"""Read port and DTOs for the order-grain Risk Queue."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from hidden_dissatisfaction.domain.queue import QueueFilters


@dataclass(frozen=True)
class QueueOrder:
    order_id: str
    risk_score: float
    risk_level: str
    status: str
    assignee_id: str | None
    assignee_name: str | None
    queued_at: datetime
    sla_due_at: datetime | None
    row_version: int
    original_queued_at: datetime | None = None
    matched_item_id: str | None = None
    top_item: object | None = None
    top_factors: tuple[object, ...] = ()
    items_count: int = 0
    outcome: str | None = None
    skip_reason: str | None = None
    self_claim_allowed: bool = False

    sla_state: str = "none"
    sla_hours_left: float | None = None
    aging_hours: float = 0.0
    total_aging_hours: float = 0.0
    is_escalated: bool = False
    is_stale: bool = False


@dataclass(frozen=True)
class QueuePage:
    items: tuple[QueueOrder, ...]
    total: int
    limit: int = 20
    offset: int = 0


class RiskOrderQueryPort(Protocol):
    """Read-only, stable Queue projection at one row per order."""

    def list_orders(self, filters: QueueFilters) -> QueuePage: ...

    def filter_options(self) -> dict[str, tuple[str, ...]]: ...


@dataclass(frozen=True)
class QueueSummary:
    """Counters and suggested case for the Risk Queue banner (FRD F02-S01)."""

    high_pending: int
    high_pending_overdue: int
    overdue: int
    escalated: int
    stale: int
    needs_decision: int
    first_pending: QueueOrder | None


def summarize_queue(
    port: RiskOrderQueryPort, *, specialist: bool, slots_left: int | None
) -> QueueSummary:
    """Build the banner from the same filters as ``GET /orders`` so both reconcile."""

    def total(**kwargs: object) -> int:
        return port.list_orders(QueueFilters(limit=1, **kwargs)).total  # type: ignore[arg-type]

    first: QueueOrder | None = None
    if not (specialist and slots_left == 0):
        # ponytail: scans the first 100 pending cases; add a level-exclusion filter if
        # a Specialist's head of queue can ever hold >100 consecutive HIGH cases.
        page = port.list_orders(QueueFilters(status="PENDING", limit=100))
        first = next((o for o in page.items if not (specialist and o.risk_level == "HIGH")), None)
    return QueueSummary(
        high_pending=total(level="HIGH", status="PENDING"),
        high_pending_overdue=total(level="HIGH", status="PENDING", sla="over"),
        overdue=total(sla="over"),
        escalated=total(sla="esc"),
        stale=total(sla="stale"),
        needs_decision=total(status="COMPLETED", needs_decision=True)
        + total(status="SKIPPED", needs_decision=True),
        first_pending=first,
    )

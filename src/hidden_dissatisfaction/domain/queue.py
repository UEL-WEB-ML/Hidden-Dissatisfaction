"""Pure query policy for the order-level Risk Queue."""

import re
from dataclasses import dataclass
from datetime import datetime


class QueueQueryValidationError(ValueError):
    """Invalid, client-supplied Queue query value."""


RISK_LEVELS = frozenset({"HIGH", "MEDIUM", "LOW"})
CASE_STATUSES = frozenset({"PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED", "OPEN"})
SORTS = frozenset({"priority", "sla", "aging"})
SLA_FILTERS = frozenset({"over", "soon", "esc", "stale"})
ORDER_PREFIX = re.compile(r"^[0-9a-f]{1,32}$")
PRODUCT_ITEM_ID = re.compile(r"^[0-9a-f]{1,32}-[1-9][0-9]*$")


@dataclass(frozen=True)
class QueueFilters:
    """Validated, order-grain Queue filter and pagination input."""

    query: str | None = None
    level: str | None = None
    status: str = "OPEN"
    assignee: str | None = None
    score_min: float | None = None
    score_max: float | None = None
    queued_from: datetime | None = None
    queued_to: datetime | None = None
    seller: str | None = None
    category: str | None = None
    outcome: str | None = None
    sla: str | None = None
    needs_decision: bool | None = None
    sort: str = "priority"
    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if self.level is not None and self.level not in RISK_LEVELS:
            raise QueueQueryValidationError("level must be HIGH, MEDIUM, or LOW")
        if self.status not in CASE_STATUSES:
            raise QueueQueryValidationError("invalid case status")
        if self.sort not in SORTS:
            raise QueueQueryValidationError("invalid Queue sort")
        if not 1 <= self.limit <= 100:
            raise QueueQueryValidationError("limit must be between 1 and 100")
        if self.offset < 0:
            raise QueueQueryValidationError("offset must not be negative")
        if self.score_min is not None and not 0 <= self.score_min <= 1:
            raise QueueQueryValidationError("smin must be between 0 and 1")
        if self.score_max is not None and not 0 <= self.score_max <= 1:
            raise QueueQueryValidationError("smax must be between 0 and 1")
        if (
            self.score_min is not None
            and self.score_max is not None
            and self.score_min > self.score_max
        ):
            raise QueueQueryValidationError("smin must not exceed smax")
        if (
            self.queued_from is not None
            and self.queued_to is not None
            and self.queued_from > self.queued_to
        ):
            raise QueueQueryValidationError("from must not be after to")
        if self.sla is not None and self.sla not in SLA_FILTERS:
            raise QueueQueryValidationError("invalid SLA filter")
        if self.outcome is not None and not re.fullmatch(
            r"(?:O:(?:HAS_ISSUE|NO_ISSUE|DUPLICATE)|S:(?:UNREACHABLE|DUPLICATE|REFUSED|NOT_APPLICABLE|OTHER))",
            self.outcome,
        ):
            raise QueueQueryValidationError("invalid outcome filter")
        if self.query is not None and not (
            ORDER_PREFIX.fullmatch(self.query) or PRODUCT_ITEM_ID.fullmatch(self.query)
        ):
            raise QueueQueryValidationError("q must be an order prefix or Product Item ID")

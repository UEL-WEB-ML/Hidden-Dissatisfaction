from typing import Any

import pytest

from hidden_dissatisfaction.application.queue import QueueOrder, QueuePage, summarize_queue
from hidden_dissatisfaction.domain.queue import QueueFilters, QueueQueryValidationError


def test_queue_defaults_to_open_priority_order() -> None:
    filters = QueueFilters()
    assert filters.status == "OPEN"
    assert filters.sort == "priority"
    assert filters.limit == 20


@pytest.mark.parametrize(
    "query",
    ["a" * 32, "a" * 32 + "-1"],
)
def test_order_prefix_and_product_item_id_are_valid(query: str) -> None:
    assert QueueFilters(query=query).query == query


@pytest.mark.parametrize(
    "kwargs",
    [
        {"level": "URGENT"},
        {"status": "CLOSED"},
        {"sort": "score"},
        {"limit": 101},
        {"offset": -1},
        {"query": "not-an-order"},
        {"score_min": 0.8, "score_max": 0.2},
        {"sla": "tomorrow"},
        {"outcome": "HAS_ISSUE"},
    ],
)
def test_invalid_queue_filters_are_rejected(kwargs: dict[str, Any]) -> None:
    with pytest.raises(QueueQueryValidationError):
        QueueFilters(**kwargs)


def _order(order_id: str, level: str) -> "QueueOrder":
    from datetime import UTC, datetime

    return QueueOrder(order_id, 0.9, level, "PENDING", None, None, datetime.now(UTC), None, 0)


class _FakeQueue:
    def __init__(self, items: list["QueueOrder"]) -> None:
        self.items = items
        self.calls: list[QueueFilters] = []

    def list_orders(self, filters: QueueFilters) -> "QueuePage":
        self.calls.append(filters)
        return QueuePage(tuple(self.items), len(self.items))

    def get_order(self, order_id: str) -> "QueueOrder | None":
        return next((item for item in self.items if item.order_id == order_id), None)

    def filter_options(self) -> dict[str, tuple[str, ...]]:
        return {}


def test_summary_first_pending_skips_high_for_specialist_but_not_manager() -> None:
    port = _FakeQueue([_order("a1", "HIGH"), _order("b2", "LOW")])
    assert summarize_queue(port, specialist=True, slots_left=2).first_pending.order_id == "b2"  # type: ignore[union-attr]
    assert summarize_queue(port, specialist=False, slots_left=None).first_pending.order_id == "a1"  # type: ignore[union-attr]


def test_summary_has_no_first_pending_when_specialist_is_at_capacity() -> None:
    port = _FakeQueue([_order("b2", "LOW")])
    assert summarize_queue(port, specialist=True, slots_left=0).first_pending is None

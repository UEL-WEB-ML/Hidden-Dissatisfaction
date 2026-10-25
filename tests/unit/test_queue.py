from typing import Any

import pytest

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

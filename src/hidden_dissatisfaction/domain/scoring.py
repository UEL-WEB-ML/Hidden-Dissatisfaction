"""Pure scoring aggregation rules."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ItemScore:
    product_item_id: str
    score: float


def aggregate_max_v1(scores: Iterable[ItemScore]) -> ItemScore:
    """Choose the maximum item score, breaking equal scores lexically."""
    values = list(scores)
    if not values:
        raise ValueError("cannot aggregate an empty score set")
    return min(values, key=lambda item: (-item.score, item.product_item_id))

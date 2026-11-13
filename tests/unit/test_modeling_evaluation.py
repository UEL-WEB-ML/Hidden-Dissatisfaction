from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hidden_dissatisfaction.modeling.evaluation import (
    _cluster_bootstrap_indices,
    aggregate_order_predictions,
    bootstrap_average_precision,
    budget_metrics,
    classification_metrics,
)


def test_classification_metrics_use_declared_threshold() -> None:
    result = classification_metrics([0, 0, 1, 1], [0.1, 0.3, 0.6, 0.9], 0.5)
    assert result["minority_precision"] == 1.0
    assert result["minority_recall"] == 1.0
    assert result["threshold"] == 0.5


def test_risk_budget_can_outperform_value_only() -> None:
    result = budget_metrics(
        [1, 0, 0, 1],
        [0.9, 0.8, 0.2, 0.1],
        [10.0, 100.0, 90.0, 1.0],
        [0.25],
    )["25%"]
    assert result["risk_recall"] == pytest.approx(0.5)
    assert result["value_only_recall"] == 0.0


def test_max_v1_aggregates_score_inherited_label_and_item_value() -> None:
    items = pd.DataFrame(
        {
            "order_id": [2, 1, 2, 1],
            "label": [1, 0, 1, 0],
            "order_value": [7.0, 3.0, 11.0, 5.0],
            "priority_score": [0.8, 0.8, 0.4, 0.9],
        }
    )
    result = aggregate_order_predictions(items)
    assert result["order_id"].tolist() == [1, 2]  # score, then deterministic order id
    assert result.loc[result.order_id == 2, "order_value"].item() == 18.0
    assert result.loc[result.order_id == 2, "priority_score"].item() == 0.8
    assert result.loc[result.order_id == 2, "label"].item() == 1


def test_budget_metrics_exposes_all_policies_and_precision() -> None:
    result = budget_metrics([1, 0, 1, 0, 0], [0.9, 0.8, 0.2, 0.1, 0.05], [2, 100, 3, 4, 5], [0.2])[
        "20%"
    ]
    assert result["risk_recall"] == pytest.approx(0.5)
    assert result["risk_precision"] == 1.0
    assert "risk_value_recall" in result
    assert "low_review_order_value_capture" in result


def test_cluster_bootstrap_is_reproducible_and_keeps_order_items_together() -> None:
    y = [1, 1, 0, 0, 1, 1]
    scores = [0.9, 0.8, 0.2, 0.1, 0.7, 0.6]
    orders = ["a", "a", "b", "b", "c", "c"]
    first = bootstrap_average_precision(y, scores, order_ids=orders, iterations=20, seed=7)
    second = bootstrap_average_precision(y, scores, order_ids=orders, iterations=20, seed=7)
    assert first == second
    assert 1 <= first["valid_iterations"] <= 20

    order_array = np.asarray(orders)
    indices = _cluster_bootstrap_indices(
        order_array, np.unique(order_array), np.random.default_rng(7)
    )
    for order in np.unique(order_array):
        assert int((order_array[indices] == order).sum()) % 2 == 0

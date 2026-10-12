from __future__ import annotations

import pytest

from hidden_dissatisfaction.modeling.evaluation import budget_metrics, classification_metrics


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

"""Classification, calibration, bootstrap, and finite-budget evaluation."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def select_f1_threshold(y_true: Sequence[int], probability: Sequence[float]) -> float:
    """Select a minority-F1 threshold without consulting final-test labels."""
    precision, recall, thresholds = precision_recall_curve(y_true, probability)
    if not len(thresholds):
        return 0.5
    denominator = precision[:-1] + recall[:-1]
    scores = np.divide(
        2 * precision[:-1] * recall[:-1],
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0,
    )
    return float(thresholds[int(np.nanargmax(scores))])


def classification_metrics(
    y_true: Sequence[int], probability: Sequence[float], threshold: float
) -> dict[str, float]:
    """Compute metrics required by the research contract."""
    y = np.asarray(y_true, dtype=int)
    proba = np.asarray(probability, dtype=float)
    predicted = (proba >= threshold).astype(int)
    return {
        "prevalence": float(y.mean()),
        "average_precision": float(average_precision_score(y, proba)),
        "roc_auc": float(roc_auc_score(y, proba)),
        "brier_score": float(brier_score_loss(y, proba)),
        "minority_precision": float(precision_score(y, predicted, zero_division=0)),
        "minority_recall": float(recall_score(y, predicted, zero_division=0)),
        "minority_f1": float(f1_score(y, predicted, zero_division=0)),
        "threshold": float(threshold),
    }


def bootstrap_average_precision(
    y_true: Sequence[int],
    probability: Sequence[float],
    *,
    iterations: int,
    seed: int,
) -> dict[str, float | int]:
    """Return a percentile interval while skipping one-class bootstrap samples."""
    y = np.asarray(y_true, dtype=int)
    proba = np.asarray(probability, dtype=float)
    generator = np.random.default_rng(seed)
    scores: list[float] = []
    for _ in range(iterations):
        indices = generator.integers(0, len(y), size=len(y))
        sampled_y = y[indices]
        if np.unique(sampled_y).size == 2:
            scores.append(float(average_precision_score(sampled_y, proba[indices])))
    if not scores:
        raise ValueError("No valid two-class bootstrap samples")
    lower, upper = np.percentile(scores, [2.5, 97.5])
    return {"lower": float(lower), "upper": float(upper), "valid_iterations": len(scores)}


def budget_metrics(
    y_true: Sequence[int],
    probability: Sequence[float],
    order_value: Sequence[float],
    budgets: Sequence[float],
) -> dict[str, dict[str, float | int]]:
    """Compare risk, value-only, and expected-random prioritization policies."""
    y = np.asarray(y_true, dtype=int)
    proba = np.asarray(probability, dtype=float)
    value = np.nan_to_num(np.asarray(order_value, dtype=float), nan=0.0)
    positive_count = int(y.sum())
    positive_value = float(value[y == 1].sum())
    risk_order = np.argsort(-proba, kind="stable")
    value_order = np.argsort(-value, kind="stable")
    result: dict[str, dict[str, float | int]] = {}
    for budget in budgets:
        selected = max(1, int(np.ceil(len(y) * budget)))
        risk_indices = risk_order[:selected]
        value_indices = value_order[:selected]
        result[f"{budget:.0%}"] = {
            "selected_orders": selected,
            "risk_recall": float(y[risk_indices].sum() / positive_count),
            "value_only_recall": float(y[value_indices].sum() / positive_count),
            "random_expected_recall": float(selected / len(y)),
            "risk_value_captured": _safe_share(
                value[risk_indices][y[risk_indices] == 1].sum(), positive_value
            ),
            "value_only_value_captured": _safe_share(
                value[value_indices][y[value_indices] == 1].sum(), positive_value
            ),
            "random_expected_value_captured": float(selected / len(y)),
        }
    return result


def _safe_share(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0

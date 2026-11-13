"""Classification, calibration, bootstrap, and finite-budget evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def aggregate_order_predictions(
    item_predictions: pd.DataFrame,
    *,
    order_id: str = "order_id",
    label: str = "label",
    order_value: str = "order_value",
    score: str = "priority_score",
) -> pd.DataFrame:
    """Aggregate item predictions using the exact max-v1 order contract.

    The order score is a priority score (not a calibrated probability). Labels
    are inherited from the order's items and value is summed once per item.
    """
    frame = item_predictions.copy()
    grouped = frame.groupby(order_id, sort=False, dropna=False)
    result = grouped.agg(
        **{label: (label, "first"), order_value: (order_value, "sum"), score: (score, "max")}
    ).reset_index()
    consistent = grouped[label].apply(lambda values: values.nunique(dropna=False) <= 1).all()
    if not bool(consistent):
        raise ValueError("item labels must be consistent within each order")
    return result.sort_values(
        [score, order_id], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)


def order_classification_metrics(
    order_predictions: pd.DataFrame, threshold: float
) -> dict[str, float]:
    """Classification metrics at order grain, retaining priority-score wording."""
    return classification_metrics(
        cast(Sequence[int], order_predictions["label"]),
        cast(Sequence[float], order_predictions["priority_score"]),
        threshold,
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
    order_ids: Sequence[object] | None = None,
) -> dict[str, float | int]:
    """Return a percentile interval; cluster-resample orders when supplied."""
    y = np.asarray(y_true, dtype=int)
    proba = np.asarray(probability, dtype=float)
    generator = np.random.default_rng(seed)
    scores: list[float] = []
    clusters = np.asarray(order_ids) if order_ids is not None else None
    unique_clusters = np.unique(clusters) if clusters is not None else None
    # Build this once: sampling a cluster must not scan the complete row array.
    cluster_groups = (
        _cluster_row_groups(clusters, unique_clusters) if clusters is not None else None
    )
    for _ in range(iterations):
        if clusters is None:
            indices = generator.integers(0, len(y), size=len(y))
        else:
            indices = _cluster_bootstrap_indices(
                clusters, unique_clusters, generator, cluster_groups=cluster_groups
            )
        sampled_y = y[indices]
        if np.unique(sampled_y).size == 2:
            scores.append(float(average_precision_score(sampled_y, proba[indices])))
    if not scores:
        raise ValueError("No valid two-class bootstrap samples")
    lower, upper = np.percentile(scores, [2.5, 97.5])
    return {"lower": float(lower), "upper": float(upper), "valid_iterations": len(scores)}


def _cluster_bootstrap_indices(
    clusters: np.ndarray,
    unique_clusters: np.ndarray | None,
    generator: np.random.Generator,
    *,
    cluster_groups: tuple[np.ndarray, ...] | None = None,
) -> np.ndarray:
    """Sample whole clusters, retaining every row belonging to each draw."""
    if unique_clusters is None:
        raise ValueError("unique clusters are required for cluster bootstrap")
    sampled = generator.choice(unique_clusters, size=len(unique_clusters), replace=True)
    groups = cluster_groups or _cluster_row_groups(clusters, unique_clusters)
    sampled_positions = np.searchsorted(unique_clusters, sampled)
    return np.concatenate([groups[int(position)] for position in sampled_positions])


def _cluster_row_groups(
    clusters: np.ndarray, unique_clusters: np.ndarray | None
) -> tuple[np.ndarray, ...]:
    """Return stable row groups aligned with ``unique_clusters`` (one scan)."""
    if unique_clusters is None:
        raise ValueError("unique clusters are required for cluster bootstrap")
    inverse = np.searchsorted(unique_clusters, clusters)
    groups: list[list[int]] = [[] for _ in unique_clusters]
    for row, group in enumerate(inverse):
        groups[int(group)].append(row)
    return tuple(np.asarray(group, dtype=int) for group in groups)


def budget_metrics(
    y_true: Sequence[int],
    probability: Sequence[float],
    order_value: Sequence[float],
    budgets: Sequence[float],
) -> dict[str, dict[str, float | int | dict[str, float]]]:
    """Compare random, value-only, risk-only, and risk×value policies."""
    y = np.asarray(y_true, dtype=int)
    proba = np.asarray(probability, dtype=float)
    value = np.nan_to_num(np.asarray(order_value, dtype=float), nan=0.0)
    positive_count = int(y.sum())
    positive_value = float(value[y == 1].sum())
    risk_order = np.argsort(-proba, kind="stable")
    value_order = np.argsort(-value, kind="stable")
    risk_value_order = np.argsort(-(proba * value), kind="stable")
    result: dict[str, dict[str, float | int | dict[str, float]]] = {}
    for budget in budgets:
        selected = max(1, int(np.ceil(len(y) * budget)))
        risk_indices = risk_order[:selected]
        value_indices = value_order[:selected]
        risk_value_indices = risk_value_order[:selected]

        def stats(indices: np.ndarray[Any, Any]) -> dict[str, float]:
            positives = int(y[indices].sum())
            return {
                "recall": float(positives / positive_count) if positive_count else 0.0,
                "precision": float(positives / len(indices)) if len(indices) else 0.0,
                "value_captured": _safe_share(
                    value[indices][y[indices] == 1].sum(), positive_value
                ),
            }

        risk_stats, value_stats, rv_stats = (
            stats(risk_indices),
            stats(value_indices),
            stats(risk_value_indices),
        )
        random_indices = np.arange(len(y))
        generator = np.random.default_rng(0)
        generator.shuffle(random_indices)
        random_stats = stats(random_indices[:selected])
        result[f"{budget:.0%}"] = {
            "selected_orders": selected,
            "random": random_stats,
            "value_only": value_stats,
            "risk_only": risk_stats,
            "risk_x_value": rv_stats,
            "risk_recall": risk_stats["recall"],
            "risk_precision": risk_stats["precision"],
            "value_only_recall": value_stats["recall"],
            "risk_value_recall": rv_stats["recall"],
            "low_review_order_value_capture": risk_stats["value_captured"],
        }
    return result


def _safe_share(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0

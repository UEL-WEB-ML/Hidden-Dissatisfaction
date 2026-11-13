"""Artifact-only rendering for the sealed model evaluation report.

This module deliberately has no dependency on the training orchestrator.  It
reads the final JSON and row-level prediction exports, then writes deterministic
figures and tables.  A priority score is described as a ranking signal unless
the saved artifact explicitly identifies it as a calibrated probability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from sklearn.calibration import calibration_curve
from sklearn.metrics import average_precision_score, precision_recall_curve

OKABE_ITO = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "sky": "#56B4E9",
    "yellow": "#F0E442",
    "black": "#000000",
}


class MissingArtifactError(FileNotFoundError):
    """Raised when a sealed input artifact is not available."""


def _require(path: Path, description: str) -> Path:
    if not path.is_file():
        raise MissingArtifactError(
            f"Missing {description}: {path}. Run the sealed final evaluation first; "
            "this renderer does not train or fit models."
        )
    return path


def _column(frame: pd.DataFrame, names: tuple[str, ...], label: str) -> str:
    for name in names:
        if name in frame.columns:
            return name
    raise ValueError(f"Prediction artifact needs {label}; tried {', '.join(names)}")


def _save_figure(fig: Figure, stem: Path) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = [stem.with_suffix(ext) for ext in (".png", ".pdf", ".svg")]
    for path in paths:
        fig.savefig(path, dpi=160 if path.suffix == ".png" else None, bbox_inches="tight")
    plt.close(fig)
    return paths


def _base_figure(title: str, xlabel: str, ylabel: str) -> tuple[Figure, Axes]:
    fig, ax = plt.subplots(figsize=(7.2, 4.6), constrained_layout=True)
    fig.patch.set_facecolor("white")
    ax.set_title(title, loc="left", weight="bold", color="#1f2933")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, color="#d9e2ec", linewidth=0.7)
    ax.set_axisbelow(True)
    return fig, ax


def _write_table(frame: pd.DataFrame, stem: Path, title: str) -> list[Path]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    clean = frame.copy().sort_values(list(frame.columns), kind="mergesort") if len(frame) else frame
    csv_path, md_path = stem.with_suffix(".csv"), stem.with_suffix(".md")
    clean.to_csv(csv_path, index=False, float_format="%.6f")

    def cell(value: Any) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{float(value):.6f}"
        return str(value).replace("|", "\\|")

    headers = [str(column) for column in clean.columns]
    lines = [
        f"# {title}",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(cell(value) for value in row) + " |"
        for row in clean.itertuples(index=False, name=None)
    )
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return [csv_path, md_path]


def _pr_curve(frame: pd.DataFrame, stem: Path) -> list[Path]:
    label = _column(frame, ("label", "negative", "target"), "the observed low-review label")
    score = _column(frame, ("probability", "priority_score", "score"), "the saved prediction score")
    y, p = frame[label].astype(int), frame[score].astype(float)
    precision, recall, _ = precision_recall_curve(y, p)
    fig, ax = _base_figure(
        "Precision–recall curve", "Recall of observed low-review orders", "Precision"
    )
    ax.plot(
        recall,
        precision,
        color=OKABE_ITO["blue"],
        linewidth=2.4,
        label=f"Average precision = {average_precision_score(y, p):.3f}",
    )
    ax.axhline(
        float(np.asarray(y, dtype=float).mean()),
        color=OKABE_ITO["orange"],
        linestyle="--",
        label="Observed prevalence",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    return _save_figure(fig, stem)


def _calibration_curve(frame: pd.DataFrame, stem: Path) -> list[Path]:
    label = _column(frame, ("label", "negative", "target"), "the observed low-review label")
    score = _column(frame, ("probability", "priority_score", "score"), "the saved prediction score")
    y, p = frame[label].astype(int), frame[score].astype(float)
    observed, predicted = calibration_curve(y, p, n_bins=10, strategy="uniform")
    fig, ax = _base_figure(
        "Calibration of saved scores", "Mean saved score", "Observed low-review rate"
    )
    ax.plot([0, 1], [0, 1], color=OKABE_ITO["black"], linestyle=":", label="Perfect calibration")
    ax.plot(
        predicted,
        observed,
        marker="o",
        color=OKABE_ITO["vermillion"],
        linewidth=2,
        label="Artifact bins",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    return _save_figure(fig, stem)


def _budget_table(order: pd.DataFrame, report: dict[str, Any]) -> pd.DataFrame:
    label = _column(order, ("label", "negative", "target"), "the observed low-review label")
    score = _column(order, ("probability", "priority_score", "score"), "the saved prediction score")
    value = _column(order, ("order_value", "value"), "order value")
    budgets = report.get("config", {}).get("budgets", (0.05, 0.10, 0.20))
    rows: list[dict[str, Any]] = []
    y, p, v = (
        order[label].astype(int).to_numpy(),
        order[score].astype(float).to_numpy(),
        order[value].astype(float).to_numpy(),
    )
    total_positive, total_value = max(int(y.sum()), 1), float(v[y == 1].sum())
    policies = {
        "risk_only": np.argsort(-p, kind="stable"),
        "value_only": np.argsort(-v, kind="stable"),
        "risk_x_value": np.argsort(-(p * v), kind="stable"),
    }
    for budget in budgets:
        n = max(1, int(np.ceil(len(order) * float(budget))))
        for policy, ranking in policies.items():
            selected = ranking[:n]
            positives = int(y[selected].sum())
            rows.append(
                {
                    "budget": f"{float(budget):.0%}",
                    "policy": policy,
                    "selected_orders": n,
                    "precision": positives / n,
                    "recall": positives / total_positive,
                    "low_review_order_value_captured": (
                        float(v[selected][y[selected] == 1].sum()) / total_value
                        if total_value
                        else 0.0
                    ),
                }
            )
    return pd.DataFrame(rows)


def render_report(
    report_path: Path,
    item_predictions_path: Path,
    order_predictions_path: Path,
    *,
    output_root: Path = Path("reports"),
) -> dict[str, list[str]]:
    """Render final artifacts only; return paths grouped by output kind."""
    report_file = _require(Path(report_path), "final JSON report")
    item_file = _require(Path(item_predictions_path), "item prediction CSV")
    order_file = _require(Path(order_predictions_path), "order prediction CSV")
    report = json.loads(report_file.read_text(encoding="utf-8"))
    items, orders = pd.read_csv(item_file), pd.read_csv(order_file)
    figures, tables = output_root / "figures", output_root / "tables"
    result: dict[str, list[str]] = {"figures": [], "tables": []}
    for path in _pr_curve(items, figures / "precision_recall_items") + _calibration_curve(
        items, figures / "calibration_items"
    ):
        result["figures"].append(str(path))
    budget = _budget_table(orders, report)
    result["tables"].extend(
        str(p)
        for p in _write_table(
            budget, tables / "budget_policy_comparison", "Budget policy comparison"
        )
    )
    fig, ax = _base_figure(
        "Recall by review budget",
        "Share of orders reviewed",
        "Recall of observed low-review orders",
    )
    for policy, color in (
        ("risk_only", "blue"),
        ("value_only", "orange"),
        ("risk_x_value", "green"),
    ):
        subset = budget[budget.policy == policy]
        ax.plot(
            subset.budget,
            subset.recall,
            marker="o",
            color=OKABE_ITO[color],
            label=policy.replace("_", " "),
        )
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    result["figures"].extend(
        str(p) for p in _save_figure(fig, figures / "budget_policy_comparison")
    )

    label_name = _column(items, ("label", "negative", "target"), "the observed low-review label")
    score_name = _column(
        items, ("probability", "priority_score", "score"), "the saved prediction score"
    )
    date_name = next(
        (
            name
            for name in ("prediction_at", "delivered_at", "order_delivered_customer_date")
            if name in items
        ),
        None,
    )
    if date_name is None:
        monthly = pd.DataFrame(
            [
                {
                    "month": "unavailable",
                    "rows": len(items),
                    "observed_low_review_rate": np.nan,
                    "mean_saved_score": np.nan,
                    "note": "prediction date is not present in the saved item artifact",
                }
            ]
        )
    else:
        monthly = (
            items.assign(
                month=pd.to_datetime(items[date_name], errors="coerce")
                .dt.to_period("M")
                .astype(str)
            )
            .groupby("month", sort=True)
            .agg(
                rows=(label_name, "size"),
                observed_low_review_rate=(label_name, "mean"),
                mean_saved_score=(score_name, "mean"),
            )
            .reset_index()
        )
    result["tables"].extend(
        str(p) for p in _write_table(monthly, tables / "monthly_evaluation", "Monthly evaluation")
    )
    subgroup_columns = [
        c
        for c in (
            "product_category",
            "customer_state",
            "seller_id",
            "seller_tenure_bucket",
            "geography",
        )
        if c in items
    ]
    if subgroup_columns:
        subgroup = (
            items.groupby(subgroup_columns[0], dropna=False, sort=True)
            .agg(
                rows=(label_name, "size"),
                observed_low_review_rate=(label_name, "mean"),
                mean_saved_score=(score_name, "mean"),
            )
            .reset_index()
            .rename(columns={subgroup_columns[0]: "subgroup"})
        )
    else:
        subgroup = pd.DataFrame(
            [
                {
                    "subgroup": "unavailable",
                    "rows": len(items),
                    "observed_low_review_rate": np.nan,
                    "mean_saved_score": np.nan,
                    "note": "no declared subgroup column is present in the saved item artifact",
                }
            ]
        )
    result["tables"].extend(
        str(p)
        for p in _write_table(subgroup, tables / "subgroup_evaluation", "Subgroup evaluation")
    )
    return result

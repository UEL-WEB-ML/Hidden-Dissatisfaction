from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from hidden_dissatisfaction.modeling.reporting import MissingArtifactError, render_report


def test_renderer_consumes_synthetic_artifacts_and_writes_all_formats(tmp_path: Path) -> None:
    report = tmp_path / "latest.json"
    report.write_text(json.dumps({"config": {"budgets": [0.5]}}), encoding="utf-8")
    items = tmp_path / "items.csv"
    pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d"],
            "label": [0, 1, 0, 1],
            "priority_score": [0.1, 0.8, 0.3, 0.7],
            "prediction_at": ["2018-01-01", "2018-01-02", "2018-02-01", "2018-02-02"],
            "product_category": ["books", "books", "toys", "toys"],
        }
    ).to_csv(items, index=False)
    orders = tmp_path / "orders.csv"
    pd.DataFrame(
        {
            "order_id": ["a", "b", "c", "d"],
            "label": [0, 1, 0, 1],
            "priority_score": [0.1, 0.8, 0.3, 0.7],
            "order_value": [10, 20, 30, 40],
        }
    ).to_csv(orders, index=False)

    result = render_report(report, items, orders, output_root=tmp_path / "reports")

    assert len(result["figures"]) == 9
    assert len(result["tables"]) == 6
    assert all(path.endswith((".png", ".pdf", ".svg")) for path in result["figures"])


def test_renderer_fails_clearly_when_sealed_artifact_is_missing(tmp_path: Path) -> None:
    with pytest.raises(MissingArtifactError, match="final JSON report"):
        render_report(tmp_path / "missing.json", tmp_path / "items.csv", tmp_path / "orders.csv")

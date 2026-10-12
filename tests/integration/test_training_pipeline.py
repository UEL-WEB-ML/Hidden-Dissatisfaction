from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from hidden_dissatisfaction.modeling.schema import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)
from hidden_dissatisfaction.modeling.training import TrainingConfig, run_training


def test_training_pipeline_writes_auditable_artifacts(tmp_path: Path) -> None:
    rows = 240
    rng = np.random.default_rng(42)
    dates = pd.date_range("2017-08-01", "2018-08-20", periods=rows)
    frame = pd.DataFrame(
        {
            "order_id": [f"order-{index}" for index in range(rows)],
            "customer_unique_id": [f"customer-{index}" for index in range(rows)],
            "main_seller": [f"seller-{index % 8}" for index in range(rows)],
            "order_purchase_timestamp": dates - pd.Timedelta(days=8),
            "order_delivered_customer_date": dates,
        }
    )
    for feature in NUMERIC_FEATURES:
        frame[feature] = rng.lognormal(mean=1.0, sigma=0.5, size=rows)
    for feature in BINARY_FEATURES:
        frame[feature] = rng.integers(0, 2, size=rows)
    for feature in CATEGORICAL_FEATURES:
        frame[feature] = rng.choice(["a", "b", "c"], size=rows)
    frame["negative"] = (np.arange(rows) % 2 == 0).astype(int)
    data_path = tmp_path / "modeling.csv"
    frame.to_csv(data_path, index=False)

    report = run_training(
        data_path,
        config=TrainingConfig(
            validation_start=datetime(2018, 1, 1),
            test_start=datetime(2018, 4, 1),
            test_end=datetime(2018, 9, 1),
            bootstrap_iterations=20,
        ),
        output_root=tmp_path,
    )

    assert report["selected_model"] in {
        "logistic_regression",
        "random_forest",
        "hist_gradient_boosting",
        "catboost",
    }
    assert (tmp_path / "artifacts/models/hidden_dissatisfaction.joblib").exists()
    assert (tmp_path / "artifacts/predictions/test_predictions.csv").exists()
    assert (tmp_path / "reports/experiments/latest.json").exists()

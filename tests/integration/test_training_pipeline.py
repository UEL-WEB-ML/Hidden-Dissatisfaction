from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from hidden_dissatisfaction.modeling.schema import (
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
)
from hidden_dissatisfaction.modeling.training import TrainingConfig, run_training


def test_training_pipeline_writes_auditable_artifacts(tmp_path: Path) -> None:
    orders = 120
    items_per_order = 2
    rows = orders * items_per_order
    rng = np.random.default_rng(42)
    order_dates = pd.date_range("2017-08-01", "2018-08-20", periods=orders)
    dates = order_dates.repeat(items_per_order)
    order_ids = [f"order-{index // items_per_order}" for index in range(rows)]
    labels = np.repeat(np.arange(orders) % 2, items_per_order)
    frame = pd.DataFrame(
        {
            "product_item_id": [f"item-{index}" for index in range(rows)],
            "order_id": order_ids,
            "order_weight": 1 / items_per_order,
            "prediction_at": dates,
            "customer_unique_id": [f"customer-{index // items_per_order}" for index in range(rows)],
            "main_seller": [f"seller-{index % 8}" for index in range(rows)],
            "order_purchase_timestamp": dates - pd.Timedelta(days=8),
            "order_delivered_customer_date": dates,
            "negative": labels,
        }
    )
    for feature in NUMERIC_FEATURES:
        frame[feature] = (
            rng.random(size=rows)
            if "negative_rate" in feature
            or feature.startswith("seller_prior_late_delivery_rate")
            or feature == "seller_prior_late_shipping_rate"
            else rng.lognormal(mean=1.0, sigma=0.5, size=rows)
        )
    for feature in BINARY_FEATURES:
        frame[feature] = rng.integers(0, 2, size=rows)
    for feature in CATEGORICAL_FEATURES:
        frame[feature] = rng.choice(["a", "b", "c"], size=rows)
    # Keep every declared model feature present in the fixture.  Derived fields
    # are recomputed by schema validation, but listing them here guards against
    # accidentally reverting this test to the old order-level contract.
    for feature in FEATURES:
        if feature not in frame:
            frame[feature] = 0
    data_path = tmp_path / "modeling.csv"
    frame.to_csv(data_path, index=False)
    data_path.with_name(data_path.name + ".manifest.json").write_text("{}", encoding="utf-8")

    report = run_training(
        data_path,
        config=TrainingConfig(
            validation_start=datetime(2018, 1, 1),
            test_start=datetime(2018, 4, 1),
            test_end=datetime(2018, 9, 1),
            bootstrap_iterations=20,
            rolling_folds=3,
        ),
        output_root=tmp_path,
    )

    assert report["selected_model"] in {
        "prevalence",
        "logistic",
        "random_forest",
        "hist_gradient_boosting",
    }
    assert report["selected_variant"]
    assert isinstance(report["selection_record"]["variant_parameters"], dict)
    assert report["partitions"]["train"]["two_class"]
    assert report["partitions"]["selection"]["two_class"]
    assert report["calibration_method"]
    assert report["threshold_policy"]
    assert "test_metrics" not in report
    assert "budget_metrics" not in report
    assert "test_diagnostics" not in report
    assert not (tmp_path / "artifacts/models/hidden_dissatisfaction.joblib").exists()
    assert not (tmp_path / "artifacts/predictions/test_predictions.csv").exists()
    assert not (tmp_path / "reports/experiments/latest.json").exists()

    try:
        run_training(
            data_path,
            config=TrainingConfig(
                validation_start=datetime(2018, 1, 1),
                test_start=datetime(2018, 4, 1),
                test_end=datetime(2018, 9, 1),
                bootstrap_iterations=1,
                rolling_folds=3,
            ),
            output_root=tmp_path,
            finalize_test=True,
        )
    except ValueError as error:
        assert "frozen selection record" in str(error)
    else:
        raise AssertionError("test finalization must require a frozen selection record")

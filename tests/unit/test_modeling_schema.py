from __future__ import annotations

import pandas as pd
import pytest

from hidden_dissatisfaction.modeling.schema import (
    FEATURES,
    ModelingDataError,
    validate_feature_list,
    validate_modeling_table,
)


def test_feature_guard_rejects_review_leakage() -> None:
    with pytest.raises(ModelingDataError, match="Forbidden model inputs"):
        validate_feature_list([*FEATURES, "review_score"])


def test_modeling_table_requires_unique_orders() -> None:
    frame = pd.DataFrame(
        {
            "order_id": ["same", "same"],
            "order_delivered_customer_date": ["2018-01-01", "2018-01-02"],
            "negative": [0, 1],
        }
    )
    with pytest.raises(ModelingDataError, match="Missing required columns"):
        validate_modeling_table(frame)

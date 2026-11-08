from __future__ import annotations

import numpy as np
import pandas as pd

from hidden_dissatisfaction.modeling.splitting import rolling_origin_splits


def test_rolling_origin_splits_expand_without_temporal_overlap() -> None:
    rows = 100
    frame = pd.DataFrame(
        {
            "order_delivered_customer_date": pd.date_range("2017-01-01", periods=rows),
            "negative": np.arange(rows) % 2,
        }
    )
    folds = rolling_origin_splits(frame, n_splits=3)
    assert len(folds) == 3
    assert [len(train) for train, _ in folds] == [40, 60, 80]
    assert [len(validation) for _, validation in folds] == [20, 20, 20]
    for train, validation in folds:
        assert (
            train.order_delivered_customer_date.max()
            < validation.order_delivered_customer_date.min()
        )

import pytest
from pydantic import ValidationError

from hidden_dissatisfaction.api.schemas import ItemDetail, TopItem


def test_top_item_metadata_is_optional_and_strict_and_item_detail_inherits_it() -> None:
    fields: dict[str, object] = {
        "product_item_id": "item-1",
        "category": None,
        "risk_score": 0.5,
        "risk_level": "MEDIUM",
        "top_factors": [],
        "synthetic_data_flag": False,
        "data_source": "model",
    }

    top_item = TopItem.model_validate(fields)
    assert top_item.threshold_version is None
    assert top_item.aggregation_rule is None

    detail = ItemDetail.model_validate(
        {**fields, "threshold_version": "threshold-v1", "aggregation_rule": "max"}
    )
    assert detail.threshold_version == "threshold-v1"
    assert detail.aggregation_rule == "max"

    with pytest.raises(ValidationError):
        TopItem.model_validate({**fields, "unexpected": True})

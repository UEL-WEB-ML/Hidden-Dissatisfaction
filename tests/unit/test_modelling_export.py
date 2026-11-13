from uuid import UUID

from hidden_dissatisfaction.application.modelling_export import (
    InvalidModellingItems,
    ModellingExportContract,
    normalize_item_records,
    validate_item_records,
)


def test_uuid_database_values_are_normalized_without_coercing_other_scalars() -> None:
    item_id = UUID("12345678-1234-5678-1234-567812345678")
    records = normalize_item_records(
        [{"product_item_id": item_id, "feature": 3.5, "timestamp": "2026-01-01"}]
    )

    assert records[0]["product_item_id"] == str(item_id)
    assert records[0]["feature"] == 3.5
    assert records[0]["timestamp"] == "2026-01-01"


def test_product_item_id_is_authoritative_order_item_key() -> None:
    contract = ModellingExportContract()
    row = {
        "product_item_id": "order-1-2",
        "order_id": "order-1",
        "order_item_id": 2,
        "prediction_at": "2026-01-01",
        "negative": 0,
        "order_weight": 1,
        "source_run_id": "run-a",
    }
    assert validate_item_records([row], contract) == [row]
    row["product_item_id"] = "run-a:order-1:2"
    try:
        validate_item_records([row], contract)
    except InvalidModellingItems:
        pass
    else:
        raise AssertionError("run-qualified product_item_id must be rejected")

"""DSN-gated integration coverage for the P6.2 Postgres writer."""

import os
from typing import Any
from uuid import uuid4

import psycopg
import pytest

from hidden_dissatisfaction.application.ports import (
    PredictionWrite,
    ReleaseMetadata,
    SourceSnapshot,
    ThresholdPolicy,
)
from hidden_dissatisfaction.infrastructure.postgres_release_scoring import (
    PostgresAtomicPredictionWriter,
)

DSN = os.environ.get("P6_TEST_POSTGRES_DSN")
pytestmark = pytest.mark.integration


def _payload(prediction_id: str, release_id: str, duplicate: bool = False) -> PredictionWrite:
    order_id = f"order-{uuid4()}"
    item_id = "item-1"
    item = {
        "order_id": order_id,
        "order_item_id": item_id,
        "product_item_id": f"{order_id}-{item_id}",
        "score": 0.91,
    }
    items = (item, item.copy()) if duplicate else (item,)
    return PredictionWrite(
        prediction_run_id=prediction_id,
        release=ReleaseMetadata(release_id, "p6.2-it-" + release_id[-8:], "gold-v1", "a" * 64),
        source=SourceSnapshot(str(uuid4()), "gold-v1", "b" * 64),
        thresholds=ThresholdPolicy("it-1", 0.5, 0.8),
        item_snapshots=items,
        order_snapshots=(
            {
                "order_id": order_id,
                "score": 0.91,
                "aggregation_rule": "max-v1",
                "top_product_item_id": item["product_item_id"],
                "top_item_score": 0.91,
                "item_count": 1,
                "item_value": 12.34,
            },
        ),
        model_input_hash="c" * 64,
    )


@pytest.fixture
def db() -> Any:
    if not DSN:
        pytest.skip("P6_TEST_POSTGRES_DSN is not set")
    release_id = str(uuid4())
    release_version = "p6.2-it-" + release_id[-8:]
    with psycopg.connect(DSN) as setup:
        setup.execute(
            """INSERT INTO ml.model_releases
            (model_release_id, release_version, model_name, model_version,
             model_artifact_uri, artifact_sha256, feature_schema_version,
             dataset_manifest_sha256, training_git_sha, source_snapshot_hash,
             training_run_id, aggregation_rule, evaluation_status)
            VALUES (%s,%s,'integration','p6.2','urn:it',%s,'gold-v1',%s,%s,%s,%s,'max-v1','CONFIRMATORY')""",
            (release_id, release_version, "a" * 64, "d" * 64, "e" * 64, "f" * 64, str(uuid4())),
        )
        setup.execute(
            "INSERT INTO ml.model_thresholds(model_release_id, threshold_version, medium_from, high_from) VALUES (%s,'it-1',.5,.8)",
            (release_id,),
        )
    with psycopg.connect(DSN) as conn:
        with conn.transaction():
            yield DSN, release_id, conn


def test_writer_persists_release_scored_snapshots(db: Any) -> None:
    dsn, release_id, conn = db
    payload = _payload(str(uuid4()), release_id)
    PostgresAtomicPredictionWriter(dsn).write(payload)
    row = conn.execute(
        "SELECT 1 FROM ml.predictions WHERE prediction_id=%s", (payload.prediction_run_id,)
    ).fetchone()
    assert row
    assert (
        conn.execute(
            "SELECT count(*) FROM ml.item_prediction_scores WHERE prediction_id=%s",
            (payload.prediction_run_id,),
        ).fetchone()[0]
        == 1
    )
    assert (
        conn.execute(
            "SELECT count(*) FROM ml.order_prediction_scores WHERE prediction_id=%s",
            (payload.prediction_run_id,),
        ).fetchone()[0]
        == 1
    )
    assert conn.execute(
        """SELECT o.top_product_item_id = i.product_item_id
        FROM ml.order_prediction_scores o JOIN ml.item_prediction_scores i
        USING (prediction_id, order_id) WHERE o.prediction_id=%s""",
        (payload.prediction_run_id,),
    ).fetchone()[0]


def test_writer_rolls_back_on_duplicate_item(db: Any) -> None:
    dsn, release_id, conn = db
    payload = _payload(str(uuid4()), release_id, duplicate=True)
    with pytest.raises(psycopg.Error):
        PostgresAtomicPredictionWriter(dsn).write(payload)
    assert (
        conn.execute(
            "SELECT count(*) FROM ml.predictions WHERE prediction_id=%s",
            (payload.prediction_run_id,),
        ).fetchone()[0]
        == 0
    )
    assert (
        conn.execute(
            "SELECT count(*) FROM ml.item_prediction_scores WHERE prediction_id=%s",
            (payload.prediction_run_id,),
        ).fetchone()[0]
        == 0
    )
    assert (
        conn.execute(
            "SELECT count(*) FROM ml.order_prediction_scores WHERE prediction_id=%s",
            (payload.prediction_run_id,),
        ).fetchone()[0]
        == 0
    )

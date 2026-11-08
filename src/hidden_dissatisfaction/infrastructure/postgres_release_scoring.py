"""Postgres adapters for immutable model releases and prediction snapshots."""

from __future__ import annotations

import json
import re

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.application.ports import (
    PredictionWrite,
    ReleaseMetadata,
    ThresholdPolicy,
)


class PostgresReleaseScoringReader:
    """Fetch exactly the explicitly requested release and threshold."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def read(
        self, release_version: str, threshold_version: str
    ) -> tuple[ReleaseMetadata, ThresholdPolicy]:
        sql = """SELECT r.model_release_id, r.release_version, r.feature_schema_version,
                         r.artifact_sha256, r.aggregation_rule,
                         t.threshold_version, t.medium_from, t.high_from
                  FROM ml.model_releases r JOIN ml.model_thresholds t
                    ON t.model_release_id = r.model_release_id
                  WHERE r.release_version = %s AND t.threshold_version = %s"""
        with psycopg.connect(self.dsn, row_factory=dict_row) as c, c.cursor() as cur:
            cur.execute(sql, (release_version, threshold_version))
            row = cur.fetchone()
        if row is None:
            raise LookupError("requested release/threshold was not found")
        return (
            ReleaseMetadata(
                str(row["model_release_id"]),
                row["release_version"],
                row["feature_schema_version"],
                row["artifact_sha256"],
                row["aggregation_rule"],
            ),
            ThresholdPolicy(
                row["threshold_version"], float(row["medium_from"]), float(row["high_from"])
            ),
        )


PostgresReleaseAndThresholdReader = PostgresReleaseScoringReader


def _json(value: object, default: object) -> object:
    return default if value is None else value


class PostgresAtomicPredictionWriter:
    """Persist a new READY run atomically; never updates an existing run."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def write(self, payload: PredictionWrite) -> None:
        hashes = (
            payload.source.input_hash,
            payload.release.model_artifact_sha256,
            payload.model_input_hash,
        )
        if any(
            not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None
            for value in hashes
        ):
            raise ValueError("source, model, and artifact hashes must be 64-character hex strings")
        model_hash = payload.model_input_hash
        with psycopg.connect(self.dsn) as c:
            with c.transaction():
                with c.cursor() as cur:
                    cur.execute(
                        """INSERT INTO ml.predictions
                        (prediction_id, model_release_id, threshold_version, source_run_id,
                         input_hash, model_input_hash, scored_at, state)
                        VALUES (%s,%s,%s,%s,%s,%s,now(),'READY')""",
                        (
                            payload.prediction_run_id,
                            payload.release.release_id,
                            payload.thresholds.threshold_version,
                            payload.source.source_run_id,
                            payload.source.input_hash,
                            model_hash,
                        ),
                    )
                    for item in payload.item_snapshots:
                        order = str(item["order_id"])
                        product = str(item["product_item_id"])
                        item_id = str(item.get("order_item_id", product.removeprefix(order + "-")))
                        cur.execute(
                            """INSERT INTO ml.item_prediction_scores
                            (prediction_id,order_id,order_item_id,product_item_id,score,risk_context,top_factors,synthetic,synthetic_metadata)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (
                                payload.prediction_run_id,
                                order,
                                item_id,
                                product,
                                item["score"],
                                json.dumps(_json(item.get("risk_context"), {})),
                                json.dumps(_json(item.get("top_factors"), [])),
                                bool(item.get("synthetic", False)),
                                json.dumps(_json(item.get("synthetic_metadata"), {})),
                            ),
                        )
                    for order_snapshot in payload.order_snapshots:
                        cur.execute(
                            """INSERT INTO ml.order_prediction_scores
                            (prediction_id,order_id,score,aggregation_rule,top_product_item_id,top_item_score,item_count,item_value,risk_context,top_factors,synthetic,synthetic_metadata)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            (
                                payload.prediction_run_id,
                                order_snapshot["order_id"],
                                order_snapshot["score"],
                                order_snapshot["aggregation_rule"],
                                order_snapshot["top_product_item_id"],
                                order_snapshot["top_item_score"],
                                order_snapshot["item_count"],
                                order_snapshot["item_value"],
                                json.dumps(_json(order_snapshot.get("risk_context"), {})),
                                json.dumps(_json(order_snapshot.get("top_factors"), [])),
                                bool(order_snapshot.get("synthetic", False)),
                                json.dumps(_json(order_snapshot.get("synthetic_metadata"), {})),
                            ),
                        )


# Descriptive alias used by integrations.
AtomicPredictionWriter = PostgresAtomicPredictionWriter

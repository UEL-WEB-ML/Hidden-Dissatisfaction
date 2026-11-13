"""Release scoring application use case (storage independent)."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol, cast

import numpy as np
import pandas as pd

from hidden_dissatisfaction.application.ports import (
    AtomicPredictionWriter,
    ModelArtifactLoader,
    PredictionWrite,
    ReleaseMetadata,
    SourceSnapshot,
    ThresholdPolicy,
)
from hidden_dissatisfaction.domain.scoring import ItemScore, aggregate_max_v1
from hidden_dissatisfaction.modeling.schema import (
    FEATURES,
    MODEL_INPUT_SCHEMA_VERSION,
    validate_runtime_model_input,
)


class Estimator(Protocol):
    def predict_proba(self, inputs: pd.DataFrame) -> object: ...


@dataclass(frozen=True)
class ReleaseScoreRequest:
    release: ReleaseMetadata
    thresholds: ThresholdPolicy
    source: SourceSnapshot
    artifact_path: Path
    items: pd.DataFrame


@dataclass(frozen=True)
class Prediction:
    prediction_id: str
    release_id: str
    product_item_id: str
    score: float
    decision: bool
    created_at: datetime
    status: str = "READY"


class ReleaseScoring:
    def __init__(self, loader: ModelArtifactLoader, writer: AtomicPredictionWriter) -> None:
        self.loader = loader
        self.writer = writer

    def score(self, request: ReleaseScoreRequest) -> tuple[Prediction, ...]:
        if not request.release.release_id or request.release.aggregation_rule != "max-v1":
            raise ValueError("invalid release")
        if request.release.required_gold_schema_version != request.source.declared_schema_version:
            raise ValueError("source schema mismatch")
        if not request.source.source_run_id or not request.source.input_hash:
            raise ValueError("invalid source snapshot")
        if not (0 <= request.thresholds.medium <= request.thresholds.high <= 1):
            raise ValueError("invalid thresholds")
        if request.items.empty or any(
            c not in request.items for c in ("order_id", "product_item_id", "price")
        ):
            raise ValueError("invalid source keys")
        if bool(request.items[["order_id", "product_item_id"]].isna().to_numpy().any()) or bool(
            request.items["product_item_id"].duplicated().any()
        ):
            raise ValueError("invalid source keys")
        envelope = self.loader.load(request.artifact_path, request.release.model_artifact_sha256)
        feature_names = cast(Sequence[str], envelope.get("feature_names", ()))
        if (
            envelope.get("model_input_schema_version") != MODEL_INPUT_SCHEMA_VERSION
            or tuple(feature_names) != FEATURES
        ):
            raise ValueError("artifact schema mismatch")
        estimator = cast(Estimator, envelope.get("estimator"))
        inputs = validate_runtime_model_input(request.items, FEATURES)
        for column in inputs.select_dtypes(include="number"):
            if not pd.Series(inputs[column]).map(lambda x: math.isfinite(float(x))).all():
                raise ValueError("non-finite model input")
        # Hash the exact, ordered values and keys supplied to predict_proba.
        hash_rows = [
            [str(order), str(product), list(values)]
            for order, product, values in zip(
                request.items["order_id"],
                request.items["product_item_id"],
                inputs.itertuples(index=False, name=None),
                strict=True,
            )
        ]
        model_input_hash = hashlib.sha256(
            json.dumps(hash_rows, separators=(",", ":"), ensure_ascii=False, default=str).encode()
        ).hexdigest()
        if not hasattr(estimator, "predict_proba"):
            raise ValueError("invalid estimator")
        raw = np.asarray(estimator.predict_proba(inputs), dtype=float)
        if getattr(raw, "ndim", 0) != 2 or raw.shape[0] != len(inputs) or raw.shape[1] < 2:
            raise ValueError("invalid probability output")
        if not np.isfinite(raw).all() or ((raw < 0) | (raw > 1)).any():
            raise ValueError("invalid probability output")
        probabilities = raw[:, 1]  # already finite and within [0, 1] (checked above)
        rows = [
            ItemScore(str(item), float(score))
            for item, score in zip(request.items["product_item_id"], probabilities, strict=True)
        ]
        grouped: dict[str, list[ItemScore]] = {}
        for row, item in zip(rows, request.items["order_id"], strict=True):
            grouped.setdefault(str(item), []).append(row)
        run_id, now = str(uuid.uuid4()), datetime.utcnow()
        items = tuple(
            {
                "prediction_run_id": run_id,
                "product_item_id": str(i),
                "order_id": str(o),
                "score": float(p),
                "source_run_id": request.source.source_run_id,
                "input_hash": request.source.input_hash,
            }
            for i, o, p in zip(
                request.items.product_item_id, request.items.order_id, probabilities, strict=True
            )
        )
        orders = []
        for order, values in grouped.items():
            chosen = aggregate_max_v1(values)
            prices = request.items.loc[request.items.order_id.astype(str) == order, "price"]
            level = (
                "HIGH"
                if chosen.score >= request.thresholds.high
                else "MEDIUM" if chosen.score >= request.thresholds.medium else "LOW"
            )
            orders.append(
                {
                    "prediction_run_id": run_id,
                    "order_id": order,
                    "score": chosen.score,
                    "top_product_item_id": chosen.product_item_id,
                    "top_item_score": chosen.score,
                    "item_count": len(values),
                    "item_value": sum(float(x) for x in prices),
                    "aggregation_rule": "max-v1",
                    "risk_level": level,
                }
            )
        payload = PredictionWrite(
            run_id,
            request.release,
            request.source,
            request.thresholds,
            items,
            tuple(orders),
            model_input_hash,
        )
        self.writer.write(payload)
        return tuple(
            Prediction(
                run_id,
                request.release.release_id,
                str(x["top_product_item_id"]),
                float(cast(float, x["score"])),
                x["risk_level"] != "LOW",
                now,
            )
            for x in orders
        )

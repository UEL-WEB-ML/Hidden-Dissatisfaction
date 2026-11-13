"""Focused release scoring contract tests."""

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from hidden_dissatisfaction.application.ports import (
    ReleaseMetadata,
    SourceSnapshot,
    ThresholdPolicy,
)
from hidden_dissatisfaction.application.release_scoring import ReleaseScoreRequest, ReleaseScoring
from hidden_dissatisfaction.infrastructure.joblib_model_artifact import (
    ModelArtifactError,
    load_model_artifact,
)
from hidden_dissatisfaction.modeling.schema import FEATURES, MODEL_INPUT_SCHEMA_VERSION


class FakeLoader:
    def __init__(self, estimator: object, **extra: object) -> None:
        self.envelope = {
            "feature_names": FEATURES,
            "model_input_schema_version": MODEL_INPUT_SCHEMA_VERSION,
            "estimator": estimator,
            **extra,
        }
        self.calls: list[tuple[Path, str]] = []

    def load(self, path: Path, expected_sha256: str) -> dict[str, object]:
        self.calls.append((path, expected_sha256))
        return self.envelope


class FakeEstimator:
    def __init__(self, scores: object) -> None:
        self.scores = scores
        self.inputs: list[pd.DataFrame] = []

    def predict_proba(self, inputs: pd.DataFrame) -> object:
        self.inputs.append(inputs)
        return self.scores


class FakeWriter:
    def __init__(self) -> None:
        self.payloads: list[Any] = []

    def write(self, payload: Any) -> None:
        self.payloads.append(payload)


def _items() -> pd.DataFrame:
    row: dict[str, object] = dict.fromkeys(FEATURES, 1.0)
    row.update({"order_id": "o2", "product_item_id": "b", "price": 12.5})
    first = row.copy()
    first.update({"order_id": "o1", "product_item_id": "z", "price": 10.0})
    return pd.DataFrame([first, row])


def _request(
    items: pd.DataFrame | None = None, medium: float = 0.5, high: float = 0.8
) -> ReleaseScoreRequest:
    return ReleaseScoreRequest(
        ReleaseMetadata("r1", "1", "p5-item-v1", "a" * 64),
        ThresholdPolicy("t1", medium, high),
        SourceSnapshot("s1", "p5-item-v1", "b" * 64),
        Path("model.joblib"),
        _items() if items is None else items,
    )


def _scores(value: float) -> list[list[float]]:
    return [[1 - value, value], [1 - value, value]]


def test_scoring_writes_complete_snapshots_and_provenance() -> None:
    writer, estimator = FakeWriter(), FakeEstimator(_scores(0.9))
    result = ReleaseScoring(FakeLoader(estimator), writer).score(_request())
    payload = writer.payloads[0]
    assert (
        len(writer.payloads) == 1
        and len({x["prediction_run_id"] for x in payload.item_snapshots}) == 1
    )
    assert {
        "prediction_run_id",
        "product_item_id",
        "order_id",
        "score",
        "source_run_id",
        "input_hash",
    } <= set(payload.item_snapshots[0])
    assert {
        "prediction_run_id",
        "order_id",
        "score",
        "top_product_item_id",
        "top_item_score",
        "item_count",
        "item_value",
        "aggregation_rule",
        "risk_level",
    } <= set(payload.order_snapshots[0])
    assert (
        payload.source.source_run_id == "s1"
        and result[0].prediction_id == payload.prediction_run_id
    )


def test_reruns_have_distinct_run_ids() -> None:
    writer = FakeWriter()
    service = ReleaseScoring(FakeLoader(FakeEstimator(_scores(0.9))), writer)
    service.score(_request())
    service.score(_request())
    assert writer.payloads[0].prediction_run_id != writer.payloads[1].prediction_run_id


def test_equal_scores_choose_lexically_first_item() -> None:
    items = _items().assign(order_id="o1").iloc[::-1].reset_index(drop=True)
    writer = FakeWriter()
    ReleaseScoring(FakeLoader(FakeEstimator(_scores(0.9))), writer).score(_request(items))
    assert writer.payloads[0].order_snapshots[0]["top_product_item_id"] == "b"


@pytest.mark.parametrize(("score", "expected"), [(0.5, "MEDIUM"), (0.8, "HIGH"), (0.49, "LOW")])
def test_threshold_boundaries(score: float, expected: str) -> None:
    writer = FakeWriter()
    ReleaseScoring(FakeLoader(FakeEstimator(_scores(score))), writer).score(
        _request(medium=0.5, high=0.8)
    )
    assert writer.payloads[0].order_snapshots[0]["risk_level"] == expected


@pytest.mark.parametrize("bad", ["shape", "nan", "range"])
def test_invalid_probability_outputs_are_rejected(bad: str) -> None:
    values: object = (
        [[0.2], [0.8]]
        if bad == "shape"
        else ([[float("nan"), 0.2], [0.8, 0.2]] if bad == "nan" else [[0.2, 1.2], [0.8, 0.2]])
    )
    with pytest.raises(ValueError, match="probability"):
        ReleaseScoring(FakeLoader(FakeEstimator(values)), FakeWriter()).score(_request())


def test_invalid_keys_and_nan_inputs_are_rejected() -> None:
    bad = _items()
    bad.loc[0, "product_item_id"] = None
    with pytest.raises(ValueError, match="source keys"):
        ReleaseScoring(FakeLoader(FakeEstimator(_scores(0.9))), FakeWriter()).score(_request(bad))
    bad = _items()
    bad.loc[0, "price"] = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        ReleaseScoring(FakeLoader(FakeEstimator(_scores(0.9))), FakeWriter()).score(_request(bad))


def test_joblib_artifact_hash_envelope_and_schema_validation(tmp_path: Path) -> None:
    import hashlib

    import joblib

    path = tmp_path / "model.joblib"
    envelope = {
        "kind": "HIDDEN_DISSATISFACTION_MODEL",
        "artifact_format_version": 1,
        "model_input_schema_version": MODEL_INPUT_SCHEMA_VERSION,
        "feature_names": FEATURES,
        "estimator": FakeEstimator(_scores(0.9)),
    }
    joblib.dump(envelope, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert load_model_artifact(path, digest)["feature_names"] == FEATURES
    with pytest.raises(ModelArtifactError, match="hash"):
        load_model_artifact(path, "0" * 64)
    joblib.dump([], path)
    with pytest.raises(ModelArtifactError, match="envelope"):
        load_model_artifact(path)
    joblib.dump({**envelope, "feature_names": ("wrong",)}, path)
    with pytest.raises(ModelArtifactError, match="schema"):
        load_model_artifact(path)


def test_request_is_immutable_and_explicit() -> None:
    request = ReleaseScoreRequest(
        ReleaseMetadata("r1", "1", "p5-item-v1", "a" * 64),
        ThresholdPolicy("t1", 0.5, 0.8),
        SourceSnapshot("s1", "p5-item-v1", "b" * 64),
        Path("model.joblib"),
        pd.DataFrame(),
    )
    assert request.release.aggregation_rule == "max-v1"
    with pytest.raises(AttributeError):
        request.release = request.release  # type: ignore[misc]

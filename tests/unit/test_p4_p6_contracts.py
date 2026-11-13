"""Branch coverage for the P4-P6 domain/application contracts (cohort, export, scoring)."""

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from hidden_dissatisfaction.application.modelling_export import (
    InvalidModellingItems,
    ModellingExportContract,
    normalize_parquet_scalar,
    validate_item_records,
)
from hidden_dissatisfaction.application.ports import (
    IOrderObservationSource,
    ReleaseMetadata,
    SourceSnapshot,
    ThresholdPolicy,
)
from hidden_dissatisfaction.application.release_scoring import ReleaseScoreRequest, ReleaseScoring
from hidden_dissatisfaction.application.summarize_cohort import SummarizePrimaryCohort
from hidden_dissatisfaction.domain.cohort import (
    CohortAssessment,
    ExclusionReason,
    OrderObservation,
)
from hidden_dissatisfaction.domain.exceptions import InvalidOrderObservationError
from hidden_dissatisfaction.domain.scoring import ItemScore, aggregate_max_v1
from hidden_dissatisfaction.modeling.schema import FEATURES, MODEL_INPUT_SCHEMA_VERSION

DELIVERED = datetime(2018, 1, 10)
ESTIMATED = datetime(2018, 1, 12)


# --- domain.cohort ---------------------------------------------------------------
def test_blank_order_id_is_rejected() -> None:
    with pytest.raises(InvalidOrderObservationError):
        OrderObservation("  ", DELIVERED, ESTIMATED)


def test_score_without_review_time_and_review_time_without_score_are_incomplete() -> None:
    score_only = OrderObservation("o", DELIVERED, ESTIMATED, review_score=1)
    time_only = OrderObservation("o", DELIVERED, ESTIMATED, review_created_at=DELIVERED)
    for observation in (score_only, time_only):
        assert observation.assess_primary_cohort().exclusion_reason is (
            ExclusionReason.INCOMPLETE_REVIEW
        )


def test_review_exactly_at_prediction_time_is_eligible_but_earlier_is_not() -> None:
    at = OrderObservation("o", DELIVERED, ESTIMATED, 2, DELIVERED).assess_primary_cohort()
    before = OrderObservation(
        "o", DELIVERED, ESTIMATED, 2, datetime(2018, 1, 9)
    ).assess_primary_cohort()
    assert at.is_eligible and at.low_review is True
    assert before.exclusion_reason is ExclusionReason.REVIEW_PRECEDES_PREDICTION


def test_assessment_invariants_are_enforced() -> None:
    with pytest.raises(InvalidOrderObservationError):
        CohortAssessment(True, None, None)
    with pytest.raises(InvalidOrderObservationError):
        CohortAssessment(True, True, ExclusionReason.LATE_DELIVERY)
    with pytest.raises(InvalidOrderObservationError):
        CohortAssessment(False, None, None)


class _Source(IOrderObservationSource):
    def __init__(self, orders: list[OrderObservation]) -> None:
        self._orders = orders

    def iter_orders(self) -> Iterable[OrderObservation]:
        return iter(self._orders)


def test_summary_counts_only_excluded_orders_with_a_reason() -> None:
    summary = SummarizePrimaryCohort(
        _Source(
            [
                OrderObservation("a", DELIVERED, ESTIMATED, 1, DELIVERED),
                OrderObservation("b", DELIVERED, ESTIMATED, 5, DELIVERED),
                OrderObservation("c", datetime(2018, 2, 1), ESTIMATED),
                OrderObservation("d", DELIVERED, ESTIMATED),
            ]
        )
    ).execute()
    assert (summary.total_orders, summary.eligible_orders, summary.low_review_orders) == (4, 2, 1)
    assert summary.exclusions == {"late_delivery": 1, "review_not_observed": 1}


def test_empty_source_yields_an_empty_summary() -> None:
    summary = SummarizePrimaryCohort(_Source([])).execute()
    assert (summary.total_orders, summary.eligible_orders, summary.exclusions) == (0, 0, {})


# --- domain.scoring --------------------------------------------------------------
def test_max_v1_rejects_empty_input_and_breaks_ties_lexically() -> None:
    with pytest.raises(ValueError):
        aggregate_max_v1([])
    best = aggregate_max_v1([ItemScore("b", 0.7), ItemScore("a", 0.7), ItemScore("c", 0.2)])
    assert best.product_item_id == "a"


# --- application.modelling_export ------------------------------------------------
def row(order: str = "o1", item: int = 1, weight: float = 1.0, **over: Any) -> dict[str, Any]:
    base = {
        "product_item_id": f"{order}-{item}",
        "order_id": order,
        "order_item_id": item,
        "prediction_at": "2018-01-10",
        "negative": 0,
        "order_weight": weight,
    }
    return {**base, **over}


CONTRACT = ModellingExportContract()


def reject(records: list[dict[str, Any]], message: str) -> None:
    with pytest.raises(InvalidModellingItems, match=message):
        validate_item_records(records, CONTRACT)


def test_scalar_normalization_recurses_into_containers() -> None:
    from uuid import UUID

    uid = UUID(int=7)
    out = normalize_parquet_scalar({"a": [uid, (uid, 1)], "b": {"c": uid}})
    assert out == {"a": [str(uid), (str(uid), 1)], "b": {"c": str(uid)}}


def test_valid_records_pass_and_weights_may_split_an_order() -> None:
    records = [row("o1", 1, 0.5), row("o1", 2, 0.5), row("o2", 1, 1.0, negative=1)]
    assert len(validate_item_records(records, CONTRACT)) == 3


@pytest.mark.parametrize(
    ("records", "message"),
    [
        ([], "empty"),
        ([row(product_item_id=None)], "nonempty"),
        ([row(product_item_id="  ")], "nonempty"),
        ([row(), row()], "unique"),
        ([{"product_item_id": "o1-1"}], "missing required fields"),
        ([row(order_id=None, product_item_id="None-1")], "order keys"),
        ([row(order_id=" ", product_item_id=" -1")], "order keys"),
        ([row(order_item_id=None, product_item_id="o1-None")], "order item keys"),
        ([row(product_item_id="o1-9")], "must equal"),
        ([row(prediction_at=None)], "prediction_at"),
        ([row(prediction_at=" ")], "prediction_at"),
        ([row(negative=None)], "non-null"),
        ([row(order_weight="heavy")], "numeric"),
        ([row(order_weight=None)], "numeric"),
        ([row(order_weight=0)], "positive"),
        ([row(order_weight=float("nan"))], "positive"),
        ([row(order_weight=float("inf"))], "positive"),
        ([row(weight=0.5)], "sum to one"),
        ([row("o1", 1, 0.5), row("o1", 2, 0.5, negative=1)], "inconsistent"),
        ([row("o1", 1, 0.5), row("o1", 2, 0.5, prediction_at="2018-02-01")], "inconsistent"),
    ],
)
def test_invalid_records_are_rejected(records: list[dict[str, Any]], message: str) -> None:
    reject(records, message)


# --- application.release_scoring -------------------------------------------------
class _Loader:
    def __init__(self, envelope: dict[str, object]) -> None:
        self.envelope = envelope

    def load(self, path: Path, expected_sha256: str) -> dict[str, object]:
        return self.envelope


class _Writer:
    def __init__(self) -> None:
        self.payloads: list[Any] = []

    def write(self, payload: Any) -> None:
        self.payloads.append(payload)


class _Model:
    def __init__(self, scores: Any = None) -> None:
        self.scores = scores

    def predict_proba(self, inputs: pd.DataFrame) -> Any:
        if self.scores is not None:
            return self.scores
        return [[0.1, 0.9]] * len(inputs)


def items(**over: Any) -> pd.DataFrame:
    frame = pd.DataFrame(
        [
            {
                **dict.fromkeys(FEATURES, 1.0),
                "order_id": "o1",
                "product_item_id": "a",
                "price": 5.0,
            },
            {
                **dict.fromkeys(FEATURES, 1.0),
                "order_id": "o1",
                "product_item_id": "b",
                "price": 7.0,
            },
        ]
    )
    for column, value in over.items():
        frame[column] = value
    return frame


def envelope(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "feature_names": FEATURES,
        "model_input_schema_version": MODEL_INPUT_SCHEMA_VERSION,
        "estimator": _Model(),
    }
    return {**base, **over}


def request(
    frame: pd.DataFrame | None = None,
    release: ReleaseMetadata | None = None,
    source: SourceSnapshot | None = None,
    thresholds: ThresholdPolicy | None = None,
) -> ReleaseScoreRequest:
    return ReleaseScoreRequest(
        release or ReleaseMetadata("r1", "1", "schema-1", "a" * 64),
        thresholds or ThresholdPolicy("t1", 0.5, 0.8),
        source or SourceSnapshot("s1", "schema-1", "b" * 64),
        Path("m.joblib"),
        items() if frame is None else frame,
    )


def refuses(req: ReleaseScoreRequest, message: str, env: dict[str, object] | None = None) -> None:
    with pytest.raises(ValueError, match=message):
        ReleaseScoring(_Loader(env or envelope()), _Writer()).score(req)


def test_scoring_rejects_invalid_release_source_and_thresholds() -> None:
    refuses(request(release=ReleaseMetadata("", "1", "schema-1", "a" * 64)), "invalid release")
    refuses(
        request(release=ReleaseMetadata("r1", "1", "schema-1", "a" * 64, "mean-v1")),
        "invalid release",
    )
    refuses(request(source=SourceSnapshot("s1", "schema-2", "b" * 64)), "schema mismatch")
    refuses(request(source=SourceSnapshot("", "schema-1", "b" * 64)), "invalid source snapshot")
    refuses(request(source=SourceSnapshot("s1", "schema-1", "")), "invalid source snapshot")
    refuses(request(thresholds=ThresholdPolicy("t", 0.9, 0.2)), "invalid thresholds")
    refuses(request(thresholds=ThresholdPolicy("t", 0.5, 1.5)), "invalid thresholds")


def test_scoring_rejects_bad_source_keys() -> None:
    refuses(request(items().iloc[0:0]), "invalid source keys")
    refuses(request(items().drop(columns=["price"])), "invalid source keys")
    refuses(request(items(order_id=[None, "o1"])), "invalid source keys")
    refuses(request(items(product_item_id=["a", "a"])), "invalid source keys")


def test_scoring_rejects_artifact_and_estimator_problems() -> None:
    refuses(request(), "artifact schema mismatch", envelope(model_input_schema_version="old"))
    refuses(request(), "artifact schema mismatch", envelope(feature_names=FEATURES[:-1]))
    refuses(request(), "invalid estimator", envelope(estimator=object()))


def test_scoring_rejects_non_finite_model_input() -> None:
    frame = items()
    frame.loc[0, FEATURES[0]] = float("inf")
    with pytest.raises(ValueError):
        ReleaseScoring(_Loader(envelope()), _Writer()).score(request(frame))


@pytest.mark.parametrize(
    "scores",
    [[[0.1, 0.9]], [[0.2, 1.4], [0.2, 0.8]], [[0.2, float("nan")], [0.2, 0.8]]],
)
def test_scoring_rejects_malformed_probabilities(scores: Any) -> None:
    refuses(request(), "invalid probability output", envelope(estimator=_Model(scores)))


def test_scoring_aggregates_each_order_to_its_maximum_and_sums_value() -> None:
    writer = _Writer()
    model = _Model([[0.7, 0.3], [0.1, 0.9]])
    ReleaseScoring(_Loader(envelope(estimator=model)), writer).score(request())
    order = writer.payloads[0].order_snapshots[0]
    assert (order["top_product_item_id"], order["top_item_score"]) == ("b", 0.9)
    assert (order["risk_level"], order["item_count"], order["item_value"]) == ("HIGH", 2, 12.0)


def test_prevalence_is_undefined_without_eligible_orders_and_exact_otherwise() -> None:
    none = SummarizePrimaryCohort(_Source([OrderObservation("d", DELIVERED, ESTIMATED)])).execute()
    assert none.low_review_prevalence is None
    half = SummarizePrimaryCohort(
        _Source(
            [
                OrderObservation("a", DELIVERED, ESTIMATED, 1, DELIVERED),
                OrderObservation("b", DELIVERED, ESTIMATED, 5, DELIVERED),
            ]
        )
    ).execute()
    assert half.low_review_prevalence == 0.5

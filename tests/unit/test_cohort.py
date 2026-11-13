"""Unit tests for primary cohort and target invariants."""

from datetime import datetime

import pytest

from hidden_dissatisfaction.domain.cohort import ExclusionReason, OrderObservation
from hidden_dissatisfaction.domain.exceptions import InvalidOrderObservationError

DELIVERED_AT = datetime(2018, 1, 10, 10, 0)
ESTIMATED_AT = datetime(2018, 1, 12)
REVIEWED_AT = datetime(2018, 1, 11)


def test_on_time_low_review_is_eligible_positive_outcome() -> None:
    """An observed 1–2 score after on-time delivery is the positive class."""
    order = OrderObservation("order-1", DELIVERED_AT, ESTIMATED_AT, 2, REVIEWED_AT)

    assessment = order.assess_primary_cohort()

    assert assessment.is_eligible is True
    assert assessment.low_review is True
    assert assessment.exclusion_reason is None


def test_on_time_high_review_is_eligible_negative_outcome() -> None:
    """An observed 3–5 score remains in the cohort as the negative class."""
    order = OrderObservation("order-1", DELIVERED_AT, ESTIMATED_AT, 5, REVIEWED_AT)

    assessment = order.assess_primary_cohort()

    assert assessment.is_eligible is True
    assert assessment.low_review is False


def test_late_delivery_is_excluded() -> None:
    """Late orders do not enter the hidden-dissatisfaction population."""
    order = OrderObservation(
        "order-1",
        datetime(2018, 1, 13),
        ESTIMATED_AT,
        1,
        datetime(2018, 1, 14),
    )

    assessment = order.assess_primary_cohort()

    assert assessment.exclusion_reason is ExclusionReason.LATE_DELIVERY


def test_missing_review_is_not_treated_as_satisfaction() -> None:
    """No-review orders are excluded rather than assigned a negative label."""
    order = OrderObservation("order-1", DELIVERED_AT, ESTIMATED_AT)

    assessment = order.assess_primary_cohort()

    assert assessment.is_eligible is False
    assert assessment.low_review is None
    assert assessment.exclusion_reason is ExclusionReason.REVIEW_NOT_OBSERVED


def test_review_before_prediction_time_is_excluded() -> None:
    """A review timestamp before delivery violates the declared prediction sequence."""
    order = OrderObservation(
        "order-1",
        DELIVERED_AT,
        ESTIMATED_AT,
        1,
        datetime(2018, 1, 9),
    )

    assessment = order.assess_primary_cohort()

    assert assessment.exclusion_reason is ExclusionReason.REVIEW_PRECEDES_PREDICTION


def test_review_score_outside_contract_raises_domain_error() -> None:
    """Observed scores outside Olist's 1–5 scale fail loudly."""
    with pytest.raises(InvalidOrderObservationError):
        OrderObservation("order-1", DELIVERED_AT, ESTIMATED_AT, 0, REVIEWED_AT)

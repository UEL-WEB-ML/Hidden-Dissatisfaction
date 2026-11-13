"""Order-level cohort and observed-label rules."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from hidden_dissatisfaction.domain.exceptions import InvalidOrderObservationError

LOW_REVIEW_SCORES = frozenset({1, 2})


class ExclusionReason(StrEnum):
    """Reason an order cannot enter the primary observed-review cohort."""

    LATE_DELIVERY = "late_delivery"
    REVIEW_NOT_OBSERVED = "review_not_observed"
    INCOMPLETE_REVIEW = "incomplete_review"
    REVIEW_PRECEDES_PREDICTION = "review_precedes_prediction"


@dataclass(frozen=True, slots=True)
class CohortAssessment:
    """Result of applying primary-cohort rules to one order."""

    is_eligible: bool
    low_review: bool | None
    exclusion_reason: ExclusionReason | None = None

    def __post_init__(self) -> None:
        """Protect consistency between eligibility, label, and exclusion reason."""
        if self.is_eligible and (self.low_review is None or self.exclusion_reason is not None):
            raise InvalidOrderObservationError(
                "Eligible assessments require a label and no exclusion."
            )
        if not self.is_eligible and self.exclusion_reason is None:
            raise InvalidOrderObservationError("Excluded assessments require an exclusion reason.")


@dataclass(frozen=True, slots=True)
class OrderObservation:
    """Information needed to establish the primary cohort and observed label."""

    order_id: str
    delivered_at: datetime
    estimated_delivery_at: datetime
    review_score: int | None = None
    review_created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate value-level invariants without applying cohort policy."""
        if not self.order_id.strip():
            raise InvalidOrderObservationError("order_id must not be blank.")
        if self.review_score is not None and self.review_score not in range(1, 6):
            raise InvalidOrderObservationError("review_score must be between 1 and 5.")

    def assess_primary_cohort(self) -> CohortAssessment:
        """Assess eligibility at delivery time and derive the observed binary outcome."""
        if self.delivered_at > self.estimated_delivery_at:
            return CohortAssessment(False, None, ExclusionReason.LATE_DELIVERY)

        has_score = self.review_score is not None
        has_review_time = self.review_created_at is not None
        if not has_score and not has_review_time:
            return CohortAssessment(False, None, ExclusionReason.REVIEW_NOT_OBSERVED)
        if has_score != has_review_time:
            return CohortAssessment(False, None, ExclusionReason.INCOMPLETE_REVIEW)

        if self.review_created_at is not None and self.review_created_at < self.delivered_at:
            return CohortAssessment(False, None, ExclusionReason.REVIEW_PRECEDES_PREDICTION)

        return CohortAssessment(
            is_eligible=True,
            low_review=self.review_score in LOW_REVIEW_SCORES,
        )

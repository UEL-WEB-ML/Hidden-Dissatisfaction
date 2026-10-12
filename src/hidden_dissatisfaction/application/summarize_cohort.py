"""Application use case for auditing primary-cohort construction."""

from collections import Counter
from dataclasses import dataclass

from hidden_dissatisfaction.application.ports import IOrderObservationSource


@dataclass(frozen=True, slots=True)
class CohortSummary:
    """Auditable counts produced while constructing the primary cohort."""

    total_orders: int
    eligible_orders: int
    low_review_orders: int
    exclusions: dict[str, int]

    @property
    def low_review_prevalence(self) -> float | None:
        """Return prevalence among eligible observed reviews, if any exist."""
        if self.eligible_orders == 0:
            return None
        return self.low_review_orders / self.eligible_orders


class SummarizePrimaryCohort:
    """Apply domain cohort rules to observations supplied by an injected port."""

    def __init__(self, source: IOrderObservationSource) -> None:
        self._source = source

    def execute(self) -> CohortSummary:
        """Return cohort counts and explicit exclusions for audit reporting."""
        total_orders = 0
        eligible_orders = 0
        low_review_orders = 0
        exclusions: Counter[str] = Counter()

        for order in self._source.iter_orders():
            total_orders += 1
            assessment = order.assess_primary_cohort()
            if assessment.is_eligible:
                eligible_orders += 1
                low_review_orders += int(assessment.low_review is True)
            elif assessment.exclusion_reason is not None:
                exclusions[assessment.exclusion_reason.value] += 1

        return CohortSummary(
            total_orders=total_orders,
            eligible_orders=eligible_orders,
            low_review_orders=low_review_orders,
            exclusions=dict(exclusions),
        )

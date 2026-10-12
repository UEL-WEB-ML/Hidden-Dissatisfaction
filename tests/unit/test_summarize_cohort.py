"""Unit tests for application-level cohort orchestration."""

from collections.abc import Iterable
from datetime import datetime

from hidden_dissatisfaction.application.ports import IOrderObservationSource
from hidden_dissatisfaction.application.summarize_cohort import SummarizePrimaryCohort
from hidden_dissatisfaction.domain.cohort import OrderObservation


class InMemoryOrderSource(IOrderObservationSource):
    """Test double that avoids filesystem and dataframe dependencies."""

    def __init__(self, orders: list[OrderObservation]) -> None:
        self._orders = orders

    def iter_orders(self) -> Iterable[OrderObservation]:
        """Yield configured observations."""
        return iter(self._orders)


def test_summary_reports_prevalence_and_exclusions() -> None:
    """The use case retains both eligible outcomes and exclusion audit counts."""
    delivered = datetime(2018, 1, 10)
    estimated = datetime(2018, 1, 12)
    reviewed = datetime(2018, 1, 11)
    source = InMemoryOrderSource(
        [
            OrderObservation("low", delivered, estimated, 1, reviewed),
            OrderObservation("high", delivered, estimated, 5, reviewed),
            OrderObservation("silent", delivered, estimated),
        ]
    )

    summary = SummarizePrimaryCohort(source).execute()

    assert summary.total_orders == 3
    assert summary.eligible_orders == 2
    assert summary.low_review_orders == 1
    assert summary.low_review_prevalence == 0.5
    assert summary.exclusions == {"review_not_observed": 1}

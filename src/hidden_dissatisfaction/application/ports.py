"""Ports required by application use cases."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from hidden_dissatisfaction.domain.cohort import OrderObservation


class IOrderObservationSource(ABC):
    """Contract for sources that provide order-level observations."""

    @abstractmethod
    def iter_orders(self) -> Iterable[OrderObservation]:
        """Yield validated order observations without assuming a storage format."""

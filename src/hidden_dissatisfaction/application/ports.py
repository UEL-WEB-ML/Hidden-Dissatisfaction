"""Ports required by application use cases."""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from hidden_dissatisfaction.domain.cohort import OrderObservation


class IOrderObservationSource(ABC):
    """Contract for sources that provide order-level observations."""

    @abstractmethod
    def iter_orders(self) -> Iterable[OrderObservation]:
        """Yield validated order observations without assuming a storage format."""


@dataclass(frozen=True)
class ReleaseMetadata:
    release_id: str
    version: str
    required_gold_schema_version: str
    model_artifact_sha256: str
    aggregation_rule: str = "max-v1"


@dataclass(frozen=True)
class ThresholdPolicy:
    threshold_version: str
    medium: float
    high: float


@dataclass(frozen=True)
class SourceSnapshot:
    source_run_id: str
    declared_schema_version: str
    input_hash: str


@dataclass(frozen=True)
class PredictionWrite:
    prediction_run_id: str
    release: ReleaseMetadata
    source: SourceSnapshot
    thresholds: ThresholdPolicy
    item_snapshots: tuple[Mapping[str, object], ...]
    order_snapshots: tuple[Mapping[str, object], ...]


class ModelArtifactLoader(Protocol):
    def load(self, path: Path, expected_sha256: str) -> Mapping[str, object]: ...


class AtomicPredictionWriter(Protocol):
    def write(self, payload: PredictionWrite) -> None: ...

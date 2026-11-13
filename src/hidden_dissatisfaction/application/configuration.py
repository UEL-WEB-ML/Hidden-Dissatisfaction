"""Use cases for the read-only P9.1 configuration surface."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from hidden_dissatisfaction.domain.configuration import (
    EffectiveParameterBundle,
    MLThresholds,
    WorkloadCapacity,
)


class ConfigurationReader(Protocol):
    def effective_parameters(self, as_of: datetime) -> EffectiveParameterBundle: ...
    def user_workload_capacity(self, user_id: UUID) -> WorkloadCapacity: ...
    def ml_thresholds(self, model_release_id: UUID, threshold_version: str) -> MLThresholds: ...


class GetEffectiveParameters:
    def __init__(self, reader: ConfigurationReader) -> None:
        self.reader = reader

    def execute(self, as_of: datetime) -> EffectiveParameterBundle:
        return self.reader.effective_parameters(as_of)


class GetUserWorkloadCapacity:
    def __init__(self, reader: ConfigurationReader) -> None:
        self.reader = reader

    def execute(self, user_id: UUID) -> WorkloadCapacity:
        return self.reader.user_workload_capacity(user_id)


class GetMLThresholds:
    def __init__(self, reader: ConfigurationReader) -> None:
        self.reader = reader

    def execute(self, model_release_id: UUID, threshold_version: str) -> MLThresholds:
        return self.reader.ml_thresholds(model_release_id, threshold_version)

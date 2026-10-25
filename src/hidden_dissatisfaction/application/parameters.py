"""Application command for append-only operational parameter versions."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from hidden_dissatisfaction.domain.parameters import validate_parameter_change


@dataclass(frozen=True)
class CreateParameterVersionCommand:
    """A Manager's request to schedule or activate one parameter value."""

    key: str
    value: object
    effective_at: datetime
    reason: str
    actor_id: UUID


@dataclass(frozen=True)
class ParameterVersion:
    """The immutable version returned after a successful append."""

    key: str
    value: str
    version: int
    effective_at: datetime
    actor_id: UUID
    reason: str
    created_at: datetime


class ParameterVersionWriter(Protocol):
    """Port whose append operation includes the corresponding audit event."""

    def effective_values(self, as_of: datetime) -> Mapping[str, str]: ...

    def append_version(
        self, command: CreateParameterVersionCommand, normalized_value: str, now: datetime
    ) -> ParameterVersion: ...


class CreateParameterVersion:
    """Validate and append a Manager-created operational parameter version."""

    def __init__(self, writer: ParameterVersionWriter) -> None:
        self._writer = writer

    def execute(self, command: CreateParameterVersionCommand, now: datetime) -> ParameterVersion:
        normalized_value = validate_parameter_change(
            key=command.key,
            value=command.value,
            effective_at=command.effective_at,
            reason=command.reason,
            now=now,
            effective_values=self._writer.effective_values(command.effective_at),
        )
        return self._writer.append_version(command, normalized_value, now)

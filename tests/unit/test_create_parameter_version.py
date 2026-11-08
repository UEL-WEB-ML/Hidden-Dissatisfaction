from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from hidden_dissatisfaction.application.parameters import (
    CreateParameterVersion,
    CreateParameterVersionCommand,
    ParameterVersion,
)
from hidden_dissatisfaction.domain.parameters import ParameterValidationError

NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)
ACTOR_ID = uuid4()


class FakeWriter:
    def __init__(self) -> None:
        self.values = {"capacity": "5", "capacity_warn": "4"}
        self.appended: tuple[CreateParameterVersionCommand, str, datetime] | None = None

    def effective_values(self, _: datetime) -> Mapping[str, str]:
        return self.values

    def append_version(
        self, command: CreateParameterVersionCommand, normalized_value: str, now: datetime
    ) -> ParameterVersion:
        self.appended = (command, normalized_value, now)
        return ParameterVersion(
            command.key,
            normalized_value,
            2,
            command.effective_at,
            command.actor_id,
            command.reason,
            now,
        )


def command(**overrides: object) -> CreateParameterVersionCommand:
    values: dict[str, object] = {
        "key": "capacity",
        "value": 6,
        "effective_at": NOW,
        "reason": "Additional shift",
        "actor_id": ACTOR_ID,
    }
    values.update(overrides)
    return CreateParameterVersionCommand(**values)  # type: ignore[arg-type]


def test_create_parameter_version_validates_then_appends() -> None:
    writer = FakeWriter()
    result = CreateParameterVersion(writer).execute(command(), NOW)

    assert result.value == "6"
    assert writer.appended is not None
    assert writer.appended[1] == "6"


def test_invalid_request_never_reaches_writer() -> None:
    writer = FakeWriter()
    with pytest.raises(ParameterValidationError):
        CreateParameterVersion(writer).execute(command(reason=""), NOW)
    assert writer.appended is None

from datetime import UTC, datetime, timedelta

import pytest

from hidden_dissatisfaction.domain.parameters import (
    ParameterValidationError,
    validate_parameter_change,
)

NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)
VALUES = {"capacity": "5", "capacity_warn": "4"}


def test_valid_integer_parameter_is_normalized() -> None:
    assert (
        validate_parameter_change(
            key="capacity",
            value=6,
            effective_at=NOW,
            reason="Additional shift",
            now=NOW,
            effective_values=VALUES,
        )
        == "6"
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [("capacity", 21), ("capacity", True), ("sla_calendar", "INVALID"), ("unknown", 1)],
)
def test_invalid_parameter_value_is_rejected(key: str, value: object) -> None:
    with pytest.raises(
        ParameterValidationError, match="Invalid|below|exceeds|integer|Unknown"
    ) as exc_info:
        validate_parameter_change(
            key=key,
            value=value,
            effective_at=NOW,
            reason="Valid reason",
            now=NOW,
            effective_values=VALUES,
        )
    assert exc_info.value.code == "PARAMETER_INVALID"


def test_reason_and_effective_time_are_required() -> None:
    with pytest.raises(ParameterValidationError) as missing_reason:
        validate_parameter_change(
            key="capacity",
            value=6,
            effective_at=NOW,
            reason=" ",
            now=NOW,
            effective_values=VALUES,
        )
    assert missing_reason.value.code == "REASON_REQUIRED"

    with pytest.raises(ParameterValidationError) as past_time:
        validate_parameter_change(
            key="capacity",
            value=6,
            effective_at=NOW - timedelta(seconds=1),
            reason="Valid reason",
            now=NOW,
            effective_values=VALUES,
        )
    assert past_time.value.code == "PARAMETER_INVALID"


def test_capacity_cross_rule_is_enforced_at_effective_time() -> None:
    with pytest.raises(ParameterValidationError, match="capacity_warn"):
        validate_parameter_change(
            key="capacity_warn",
            value=5,
            effective_at=NOW,
            reason="Invalid warning level",
            now=NOW,
            effective_values=VALUES,
        )

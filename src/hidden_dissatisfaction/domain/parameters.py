"""Pure validation policies for append-only operational parameters."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ParameterDefinition:
    """The immutable contract for one configurable operational value."""

    key: str
    unit: str
    minimum: int | None = None
    maximum: int | None = None
    allowed_values: frozenset[str] = frozenset()


class ParameterValidationError(ValueError):
    """A validation error with the stable API Contract error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


PARAMETER_DEFINITIONS: dict[str, ParameterDefinition] = {
    "sla_calendar": ParameterDefinition(
        "sla_calendar", "enum", allowed_values=frozenset({"CALENDAR", "BUSINESS_HOURS"})
    ),
    "sla_hours_high": ParameterDefinition("sla_hours_high", "hours", 1, 720),
    "sla_hours_medium": ParameterDefinition("sla_hours_medium", "hours", 1, 720),
    "sla_hours_low": ParameterDefinition("sla_hours_low", "hours", 1, 720),
    "first_touch_hours": ParameterDefinition("first_touch_hours", "hours", 1, 720),
    "soon_hours": ParameterDefinition("soon_hours", "hours", 1, 720),
    "stale_hours": ParameterDefinition("stale_hours", "hours", 1, 720),
    "capacity": ParameterDefinition("capacity", "orders", 1, 20),
    "capacity_warn": ParameterDefinition("capacity_warn", "orders", 1, 20),
    "max_contact": ParameterDefinition("max_contact", "times", 1, 10),
    "reopen_review_times": ParameterDefinition("reopen_review_times", "times", 1, 10),
    "retry_gap_days": ParameterDefinition("retry_gap_days", "days", 1, 60),
    "aging_days": ParameterDefinition("aging_days", "days", 1, 60),
    "reopen_review_days": ParameterDefinition("reopen_review_days", "days", 1, 60),
}


def validate_parameter_change(
    *,
    key: str,
    value: object,
    effective_at: datetime,
    reason: str,
    now: datetime,
    effective_values: Mapping[str, str],
) -> str:
    """Validate and normalize one new parameter version without mutating state."""
    if not reason.strip():
        raise ParameterValidationError("REASON_REQUIRED", "A reason is required")
    if effective_at.tzinfo is None or now.tzinfo is None:
        raise ParameterValidationError("PARAMETER_INVALID", "effective_at must include a timezone")
    if effective_at < now:
        raise ParameterValidationError("PARAMETER_INVALID", "effective_at must not be in the past")

    definition = PARAMETER_DEFINITIONS.get(key)
    if definition is None:
        raise ParameterValidationError("PARAMETER_INVALID", "Unknown parameter key")

    normalized = _normalize_value(definition, value)
    values = dict(effective_values)
    values[key] = normalized
    _validate_cross_rules(values)
    return normalized


def _normalize_value(definition: ParameterDefinition, value: object) -> str:
    if definition.unit == "enum":
        if isinstance(value, str) and value in definition.allowed_values:
            return value
        raise ParameterValidationError("PARAMETER_INVALID", f"Invalid value for {definition.key}")

    if isinstance(value, bool) or not isinstance(value, int):
        raise ParameterValidationError("PARAMETER_INVALID", f"{definition.key} must be an integer")
    if definition.minimum is not None and value < definition.minimum:
        raise ParameterValidationError(
            "PARAMETER_INVALID", f"{definition.key} is below its minimum"
        )
    if definition.maximum is not None and value > definition.maximum:
        raise ParameterValidationError("PARAMETER_INVALID", f"{definition.key} exceeds its maximum")
    return str(value)


def _validate_cross_rules(values: Mapping[str, str]) -> None:
    try:
        capacity = int(values["capacity"])
        capacity_warn = int(values["capacity_warn"])
    except KeyError:
        return
    except ValueError as exc:
        raise ParameterValidationError(
            "PARAMETER_INVALID", "Capacity values must be integers"
        ) from exc
    if capacity_warn >= capacity:
        raise ParameterValidationError(
            "PARAMETER_INVALID", "capacity_warn must be lower than capacity"
        )

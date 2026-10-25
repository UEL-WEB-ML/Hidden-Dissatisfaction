"""Pure P9 workflow policies; persistence and HTTP remain outside this module."""

from dataclasses import dataclass
from datetime import datetime, timedelta


class WorkflowPolicyError(ValueError):
    """A rejected workflow action with its stable API Contract code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


OPEN_STATUSES = frozenset({"PENDING", "IN_PROGRESS"})
CLOSED_STATUSES = frozenset({"COMPLETED", "SKIPPED"})
OUTCOMES = frozenset({"HAS_ISSUE", "NO_ISSUE", "DUPLICATE"})
SKIP_REASONS = frozenset({"UNREACHABLE", "DUPLICATE", "REFUSED", "NOT_APPLICABLE", "OTHER"})
CONTACT_RESULTS = frozenset({"REACHED", "NO_ANSWER", "CALLBACK", "WRONG_NUMBER"})


@dataclass(frozen=True)
class CaseSnapshot:
    """Minimal state required to validate a write workflow command."""

    status: str
    risk_level: str
    assignee_id: str | None
    contact_count: int
    max_contact: int
    closed_at: datetime | None
    reopen_count: int


def validate_claim(case: CaseSnapshot, actor_id: str, active_count: int, capacity: int) -> None:
    """Enforce the Specialist self-claim rules before a conditional database update."""
    if case.status != "PENDING" or case.assignee_id is not None:
        raise WorkflowPolicyError("INVALID_STATE", "Only unassigned pending cases can be claimed")
    if case.risk_level == "HIGH":
        raise WorkflowPolicyError(
            "HIGH_RISK_REQUIRES_ASSIGN", "High-risk cases require Manager assignment"
        )
    if active_count >= capacity:
        raise WorkflowPolicyError("CAPACITY_FULL", "Specialist capacity is full")
    if not actor_id:
        raise WorkflowPolicyError("FORBIDDEN", "An authenticated Specialist is required")


def validate_close(
    case: CaseSnapshot, outcome: str | None, skip_reason: str | None, note: str | None
) -> None:
    """Validate a complete or skip transition from an active case."""
    if case.status != "IN_PROGRESS":
        raise WorkflowPolicyError("INVALID_STATE", "Only in-progress cases can be closed")
    if (outcome is None) == (skip_reason is None):
        raise WorkflowPolicyError("VALIDATION_ERROR", "Exactly one close result is required")
    if outcome is not None and outcome not in OUTCOMES:
        raise WorkflowPolicyError("VALIDATION_ERROR", "Invalid completion outcome")
    if skip_reason is not None:
        if skip_reason not in SKIP_REASONS:
            raise WorkflowPolicyError("VALIDATION_ERROR", "Invalid skip reason")
        if skip_reason == "OTHER" and not (note or "").strip():
            raise WorkflowPolicyError("VALIDATION_ERROR", "A note is required for OTHER")


def validate_contact(
    case: CaseSnapshot, contacted_at: datetime, now: datetime, result: str
) -> bool:
    """Validate an append-only contact and return whether it must auto-skip."""
    if case.status != "IN_PROGRESS":
        raise WorkflowPolicyError("INVALID_STATE", "Contacts require an in-progress case")
    if contacted_at.tzinfo is None or contacted_at > now:
        raise WorkflowPolicyError("VALIDATION_ERROR", "contacted_at must not be in the future")
    if result not in CONTACT_RESULTS:
        raise WorkflowPolicyError("VALIDATION_ERROR", "Invalid contact result")
    if case.contact_count >= case.max_contact:
        raise WorkflowPolicyError("MAX_CONTACTS_REACHED", "Maximum contacts reached")
    return case.contact_count + 1 == case.max_contact and result != "REACHED"


def validate_reopen(
    case: CaseSnapshot, now: datetime, review_days: int, review_times: int, confirmed: bool
) -> None:
    """Enforce the confirmation threshold for reopening a closed case."""
    if case.status not in CLOSED_STATUSES or case.closed_at is None:
        raise WorkflowPolicyError("INVALID_STATE", "Only closed cases can be reopened")
    overdue = now - case.closed_at > timedelta(days=review_days)
    if (overdue or case.reopen_count >= review_times) and not confirmed:
        raise WorkflowPolicyError("REVIEW_CONFIRMATION_REQUIRED", "Review confirmation is required")

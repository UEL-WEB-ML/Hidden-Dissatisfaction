"""Pure P9 workflow policies; persistence and HTTP remain outside this module."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta


class WorkflowPolicyError(ValueError):
    """A rejected workflow action with its stable API Contract code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class CaseNotFoundError(LookupError):
    """The requested order has no workflow case."""


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
    if contacted_at.tzinfo is None:
        raise WorkflowPolicyError("VALIDATION_ERROR", "contacted_at must include a timezone")
    if contacted_at > now:
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


DECISIONS = frozenset(
    {"NO_FURTHER_ACTION", "FOLLOW_UP_CUSTOMER", "WORK_WITH_SELLER", "REFER_AFTER_SALES"}
)
CONTACT_METHODS = frozenset({"PHONE", "EMAIL", "MESSAGE"})
MAX_COMMENT_LENGTH = 1000
MAX_EVIDENCE_FILES = 3
MAX_EVIDENCE_BYTES = 5 * 1024 * 1024
_EVIDENCE_SIGNATURES = (
    ("image/png", "png", b"\x89PNG\r\n\x1a\n"),
    ("image/jpeg", "jpg", b"\xff\xd8\xff"),
    ("application/pdf", "pdf", b"%PDF-"),
)


def require_reason(reason: str | None) -> str:
    """Return the trimmed reason or raise the contract's ``REASON_REQUIRED``."""
    if not (reason or "").strip():
        raise WorkflowPolicyError("REASON_REQUIRED", "A reason is required")
    return str(reason).strip()


def validate_assign(
    status: str,
    previous_assignee_id: str | None,
    assignee_id: str,
    reason: str | None,
    active_count: int,
    capacity: int,
    override_capacity: bool,
) -> bool:
    """Validate a Manager assign/reassign and return whether it overrides capacity."""
    if status not in OPEN_STATUSES:
        raise WorkflowPolicyError("INVALID_STATE", "Closed cases cannot be assigned")
    if previous_assignee_id == assignee_id:
        raise WorkflowPolicyError("INVALID_STATE", "The case is already assigned to this user")
    if previous_assignee_id is not None:
        require_reason(reason)
    if active_count < capacity:
        return False
    if not override_capacity:
        raise WorkflowPolicyError("CAPACITY_FULL", "Specialist capacity is full")
    require_reason(reason)
    return True


def validate_comment(text: str | None) -> str:
    """Return the trimmed comment, enforcing the 1-1000 character contract."""
    value = (text or "").strip()
    if not value or len(value) > MAX_COMMENT_LENGTH:
        raise WorkflowPolicyError("VALIDATION_ERROR", "Comment must be 1-1000 characters")
    return value


def validate_decision(
    status: str,
    decision: str | None,
    reason: str | None,
    next_step: str | None,
    due_date: date | None,
    today: date,
) -> None:
    """Validate the three mandatory Manager Decision fields and the due date."""
    if status not in CLOSED_STATUSES:
        raise WorkflowPolicyError("INVALID_STATE", "Decisions require a closed case")
    if decision not in DECISIONS:
        raise WorkflowPolicyError("VALIDATION_ERROR", "Invalid decision")
    require_reason(reason)
    if not (next_step or "").strip():
        raise WorkflowPolicyError("VALIDATION_ERROR", "next_step is required")
    if due_date is not None and due_date < today:
        raise WorkflowPolicyError("VALIDATION_ERROR", "due_date must not be in the past")


def validate_contact_inputs(
    method: str, contacted_at: datetime, next_contact_date: date | None, file_count: int
) -> None:
    """Validate the Attempt fields that do not depend on stored case state."""
    if method not in CONTACT_METHODS:
        raise WorkflowPolicyError("VALIDATION_ERROR", "Invalid contact method")
    if next_contact_date is not None and next_contact_date < contacted_at.date():
        raise WorkflowPolicyError("VALIDATION_ERROR", "next_contact_date precedes the contact")
    if file_count > MAX_EVIDENCE_FILES:
        raise WorkflowPolicyError("EVIDENCE_INVALID", "At most 3 evidence files per Attempt")


def detect_evidence_type(head: bytes, size: int) -> tuple[str, str]:
    """Return ``(content_type, extension)`` from the file signature, never the client's claim."""
    if not 0 < size <= MAX_EVIDENCE_BYTES:
        raise WorkflowPolicyError("EVIDENCE_INVALID", "Evidence must be 1 byte to 5 MB")
    for content_type, extension, signature in _EVIDENCE_SIGNATURES:
        if head.startswith(signature):
            return content_type, extension
    raise WorkflowPolicyError("EVIDENCE_INVALID", "Evidence must be PNG, JPG or PDF")

"""Write-side ports for the P9 case workflow (assign, close, reopen, notes, contacts)."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class EvidenceRef:
    """An uploaded file referenced by an Attempt."""

    file_id: UUID


@dataclass(frozen=True)
class AddContact:
    """Append-only Attempt input for the current assignee."""

    order_id: str
    actor_id: UUID
    contacted_at: datetime
    method: str
    result: str
    note: str | None
    next_contact_date: date | None
    evidence_ref: str | None
    evidence: tuple[EvidenceRef, ...]


@dataclass(frozen=True)
class ContactResult:
    """Outcome of an Attempt, including whether it auto-skipped the case."""

    attempt_no: int
    auto_skipped: bool


@dataclass(frozen=True)
class AssignResult:
    """The previous holder's name, for the API's ``previous_assignee_name``."""

    previous_assignee_name: str | None


@dataclass(frozen=True)
class AddDecision:
    """Manager Decision input; always attached to the current review cycle."""

    order_id: str
    actor_id: UUID
    decision: str
    reason: str
    next_step: str
    next_step_assignee_id: UUID | None
    due_date: date | None
    note: str | None


class WorkflowCommands(Protocol):
    """Transactional write use cases; each method is one database transaction."""

    def assign(
        self,
        order_id: str,
        actor_id: UUID,
        assignee_id: UUID,
        reason: str | None,
        override_capacity: bool,
    ) -> AssignResult: ...

    def complete(
        self, order_id: str, actor_id: UUID, is_manager: bool, outcome: str, note: str | None
    ) -> None: ...

    def skip(
        self, order_id: str, actor_id: UUID, is_manager: bool, reason: str, note: str | None
    ) -> None: ...

    def reopen(
        self, order_id: str, actor_id: UUID, reason: str | None, review_confirmed: bool
    ) -> None: ...

    def add_comment(
        self, order_id: str, actor_id: UUID, is_manager: bool, text: str
    ) -> dict[str, object]: ...

    def add_model_note(self, order_id: str, actor_id: UUID, note: str) -> dict[str, object]: ...

    def add_contact(self, command: AddContact) -> ContactResult: ...

    def add_decision(self, command: AddDecision) -> dict[str, object]: ...

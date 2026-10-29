"""HTTP routes for Order Detail, workflow writes, evidence, Dashboard and Audit (P9.3-P9.8)."""

from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Annotated, Any, Protocol, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from hidden_dissatisfaction.application.workflow_commands import (
    AddContact,
    AddDecision,
    EvidenceRef,
    WorkflowCommands,
)
from hidden_dissatisfaction.domain.auth import Role, User
from hidden_dissatisfaction.domain.workflow import (
    MAX_EVIDENCE_BYTES,
    CaseNotFoundError,
    WorkflowPolicyError,
)
from hidden_dissatisfaction.infrastructure.local_evidence_store import (
    EvidenceAccessError,
    EvidenceNotFoundError,
)

from .authorization import require_manager

T = TypeVar("T")
_FORBIDDEN_CODES = {"FORBIDDEN", "HIGH_RISK_REQUIRES_ASSIGN"}
_CONFLICT_CODES = {"INVALID_STATE", "ALREADY_CLAIMED"}


class CaseReads(Protocol):
    """Read projections consumed by these routes."""

    def detail(self, order_id: str, now: datetime, include_audit: bool) -> dict[str, Any]: ...
    def dashboard(
        self,
        now: datetime,
        *,
        days: int | None,
        level: str | None,
        seller: str | None,
        category: str | None,
        assignee: str | None,
        status: str | None,
        product_item: str | None,
        view: str,
    ) -> dict[str, Any]: ...

    def audit_events(
        self,
        *,
        event_type: str | None,
        actor_id: str | None,
        order_id: str | None,
        override_only: bool,
        limit: int,
        offset: int,
    ) -> dict[str, Any]: ...


class EvidenceFiles(Protocol):
    """Evidence storage port."""

    def save(self, owner_id: UUID, file_name: str | None, data: bytes) -> dict[str, Any]: ...
    def locate(self, upload_id: UUID, user_id: UUID, is_manager: bool) -> tuple[Any, str, str]: ...


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssignBody(_Body):
    assignee_id: UUID
    reason: str | None = None
    override_capacity: bool = False


class CompleteBody(_Body):
    outcome: str
    note: str | None = None


class SkipBody(_Body):
    reason: str
    note: str | None = None


class ReopenBody(_Body):
    reason: str | None = None
    review_confirmed: bool = False


class TextBody(_Body):
    text: str


class NoteBody(_Body):
    note: str


class EvidenceBody(_Body):
    file_id: UUID
    file_name: str | None = None
    file_type: str | None = None
    file_size: int | None = None


class ContactBody(_Body):
    contacted_at: datetime
    method: str
    result: str
    note: str | None = None
    next_contact_date: date | None = None
    evidence: list[EvidenceBody] = []
    evidence_ref: str | None = None


class DecisionBody(_Body):
    decision: str
    reason: str | None = None
    next_step: str | None = None
    next_step_assignee_id: UUID | None = None
    due_date: date | None = None
    note: str | None = None


def _error(http_status: int, code: str, message: str) -> HTTPException:
    return HTTPException(http_status, detail={"code": code, "message": message, "details": None})


def policy_error(exc: WorkflowPolicyError) -> HTTPException:
    """Map a domain rejection to the API Contract status and code."""
    if exc.code in _FORBIDDEN_CODES:
        http_status = status.HTTP_403_FORBIDDEN
    elif exc.code in _CONFLICT_CODES:
        http_status = status.HTTP_409_CONFLICT
    else:
        http_status = status.HTTP_422_UNPROCESSABLE_ENTITY
    return _error(http_status, exc.code, str(exc))


def build_workflow_router(
    current_user: Callable[..., Any],
    commands: WorkflowCommands,
    reads: CaseReads,
    evidence: EvidenceFiles,
) -> APIRouter:
    """Wire the routes to injected ports; routes only parse, authorize, delegate and map."""
    router = APIRouter(prefix="/api/v1")
    Authenticated = Annotated[User, Depends(current_user)]

    def run(call: Callable[[], T]) -> T:
        try:
            return call()
        except CaseNotFoundError as exc:
            raise _error(404, "ORDER_NOT_FOUND", "Order not found") from exc
        except WorkflowPolicyError as exc:
            raise policy_error(exc) from exc

    def order_of(order_id: str, user: User) -> dict[str, Any]:
        detail: dict[str, Any] = run(lambda: reads.detail(order_id, datetime.now(UTC), False))
        order: dict[str, Any] = detail["order"]
        return order

    @router.get("/orders/{order_id}")
    async def order_detail(order_id: str, user: Authenticated) -> dict[str, Any]:
        detail: dict[str, Any] = run(
            lambda: reads.detail(order_id, datetime.now(UTC), user.role is Role.MANAGER)
        )
        return detail

    @router.post("/orders/{order_id}/assign")
    async def assign(order_id: str, body: AssignBody, user: Authenticated) -> dict[str, Any]:
        require_manager(user)
        result = run(
            lambda: commands.assign(
                order_id, user.id, body.assignee_id, body.reason, body.override_capacity
            )
        )
        return {
            "order": order_of(order_id, user),
            "previous_assignee_name": result.previous_assignee_name,
        }

    @router.post("/orders/{order_id}/complete")
    async def complete(order_id: str, body: CompleteBody, user: Authenticated) -> dict[str, Any]:
        run(
            lambda: commands.complete(
                order_id, user.id, user.role is Role.MANAGER, body.outcome, body.note
            )
        )
        return {"order": order_of(order_id, user)}

    @router.post("/orders/{order_id}/skip")
    async def skip(order_id: str, body: SkipBody, user: Authenticated) -> dict[str, Any]:
        run(
            lambda: commands.skip(
                order_id, user.id, user.role is Role.MANAGER, body.reason, body.note
            )
        )
        return {"order": order_of(order_id, user)}

    @router.post("/orders/{order_id}/reopen")
    async def reopen(order_id: str, body: ReopenBody, user: Authenticated) -> dict[str, Any]:
        require_manager(user)
        run(lambda: commands.reopen(order_id, user.id, body.reason, body.review_confirmed))
        return {"order": order_of(order_id, user)}

    @router.post("/orders/{order_id}/comments", status_code=201)
    async def comment(order_id: str, body: TextBody, user: Authenticated) -> dict[str, Any]:
        saved = run(
            lambda: commands.add_comment(order_id, user.id, user.role is Role.MANAGER, body.text)
        )
        return {
            **saved,
            "author_id": user.id,
            "author_name": user.full_name,
            "author_role": user.role.value,
        }

    @router.post("/orders/{order_id}/model-notes", status_code=201)
    async def model_note(order_id: str, body: NoteBody, user: Authenticated) -> dict[str, Any]:
        require_manager(user)
        return run(lambda: commands.add_model_note(order_id, user.id, body.note))

    @router.post("/orders/{order_id}/contacts", status_code=201)
    async def add_contact(order_id: str, body: ContactBody, user: Authenticated) -> dict[str, Any]:
        if user.role is not Role.SPECIALIST:
            raise _error(403, "FORBIDDEN", "Only the assigned Specialist can add contacts")
        run(
            lambda: commands.add_contact(
                AddContact(
                    order_id,
                    user.id,
                    body.contacted_at,
                    body.method,
                    body.result,
                    body.note,
                    body.next_contact_date,
                    body.evidence_ref,
                    tuple(EvidenceRef(e.file_id) for e in body.evidence),
                )
            )
        )
        detail = run(lambda: reads.detail(order_id, datetime.now(UTC), False))
        return {"contact": detail["contacts"][-1], "order": detail["order"]}

    @router.post("/orders/{order_id}/decisions", status_code=201)
    async def add_decision(
        order_id: str, body: DecisionBody, user: Authenticated
    ) -> dict[str, Any]:
        require_manager(user)
        saved = run(
            lambda: commands.add_decision(
                AddDecision(
                    order_id,
                    user.id,
                    body.decision,
                    body.reason or "",
                    body.next_step or "",
                    body.next_step_assignee_id,
                    body.due_date,
                    body.note,
                )
            )
        )
        return {
            "decision": {**saved, "actor_id": user.id, "actor_name": user.full_name},
            "order": order_of(order_id, user),
        }

    @router.post("/files", status_code=201)
    async def upload(user: Authenticated, file: Annotated[UploadFile, File()]) -> dict[str, Any]:
        if user.role is not Role.SPECIALIST:
            raise _error(403, "FORBIDDEN", "Only Specialists upload evidence")
        data = await file.read(MAX_EVIDENCE_BYTES + 1)  # never buffer more than the limit + 1
        return run(lambda: evidence.save(user.id, file.filename, data))

    @router.get("/files/{file_id}")
    async def download(file_id: UUID, user: Authenticated) -> FileResponse:
        try:
            path, content_type, name = evidence.locate(file_id, user.id, user.role is Role.MANAGER)
        except EvidenceNotFoundError as exc:
            raise _error(404, "FILE_NOT_FOUND", "File not found") from exc
        except EvidenceAccessError as exc:
            raise _error(403, "FORBIDDEN", "Not allowed to open this file") from exc
        return FileResponse(path, media_type=content_type, filename=name)

    @router.get("/dashboard")
    async def dashboard(
        user: Authenticated,
        days: Annotated[int | None, Query()] = None,
        level: str | None = None,
        seller: str | None = None,
        category: str | None = None,
        assignee: str | None = None,
        status_filter: Annotated[str | None, Query(alias="status")] = None,
        product_item: str | None = None,
        view: str = "order",
    ) -> dict[str, Any]:
        require_manager(user)
        if days not in (None, 1, 3, 7) or view not in ("order", "product"):
            raise _error(422, "VALIDATION_ERROR", "days must be 1, 3 or 7; view order|product")
        return reads.dashboard(
            datetime.now(UTC),
            days=days,
            level=level,
            seller=seller,
            category=category,
            assignee=assignee,
            status=status_filter,
            product_item=product_item,
            view=view,
        )

    @router.get("/audit-events")
    async def audit_events(
        user: Authenticated,
        event_type: str | None = None,
        actor_id: str | None = None,
        order_id: str | None = None,
        override_only: bool = False,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> dict[str, Any]:
        require_manager(user)
        return reads.audit_events(
            event_type=event_type,
            actor_id=actor_id,
            order_id=order_id,
            override_only=override_only,
            limit=limit,
            offset=offset,
        )

    return router

"""HTTP-layer contract tests for the P9 workflow routes using in-memory fake ports."""

from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from hidden_dissatisfaction.api.app import create_app  # noqa: E402
from hidden_dissatisfaction.api.config import Settings  # noqa: E402
from hidden_dissatisfaction.application.workflow_commands import (  # noqa: E402
    AddContact,
    AddDecision,
    AssignResult,
    ContactResult,
)
from hidden_dissatisfaction.domain.auth import AccessToken, InvalidToken, Role, User  # noqa: E402
from hidden_dissatisfaction.domain.workflow import (  # noqa: E402
    CaseNotFoundError,
    WorkflowPolicyError,
)
from hidden_dissatisfaction.infrastructure.local_evidence_store import (  # noqa: E402
    EvidenceAccessError,
    sanitize_file_name,
)

NOW = datetime(2026, 10, 25, tzinfo=UTC)
SPECIALIST = User(uuid4(), "spec", "h", True, "vi", "Spec", Role.SPECIALIST, NOW)
MANAGER = User(uuid4(), "boss", "h", True, "vi", "Boss", Role.MANAGER, NOW)
USERS = {"specialist": SPECIALIST, "manager": MANAGER}


class FakeAuth:
    async def login(self, username: str, password: str) -> AccessToken:
        return AccessToken("specialist", NOW)

    async def identify(self, token: str) -> User:
        if token not in USERS:
            raise InvalidToken
        return USERS[token]

    async def update_preferred_language(self, user: User, language: str) -> User:
        return user


class FakeCommands:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.error: Exception | None = None

    def _go(self, name: str, *args: Any) -> None:
        self.calls.append((name, args))
        if self.error:
            raise self.error

    def assign(self, *args: Any) -> AssignResult:
        self._go("assign", *args)
        return AssignResult("Old Holder")

    def complete(self, *args: Any) -> None:
        self._go("complete", *args)

    def skip(self, *args: Any) -> None:
        self._go("skip", *args)

    def reopen(self, *args: Any) -> None:
        self._go("reopen", *args)

    def add_comment(self, *args: Any) -> dict[str, object]:
        self._go("comment", *args)
        return {"text": args[-1], "created_at": NOW.isoformat()}

    def add_model_note(self, *args: Any) -> dict[str, object]:
        self._go("note", *args)
        return {"note": args[-1], "created_at": NOW.isoformat()}

    def add_contact(self, command: AddContact) -> ContactResult:
        self._go("contact", command)
        return ContactResult(1, False)

    def add_decision(self, command: AddDecision) -> dict[str, object]:
        self._go("decision", command)
        return {"decision": command.decision, "cycle_no": 1}


class FakeReads:
    def __init__(self) -> None:
        self.include_audit: bool | None = None
        self.missing = False
        self.omit_collection: str | None = None

    def detail(self, order_id: str, now: datetime, include_audit: bool) -> dict[str, Any]:
        if self.missing:
            raise CaseNotFoundError(order_id)
        self.include_audit = include_audit
        item = {
            "product_item_id": "item-1",
            "category": "electronics",
            "risk_score": 0.8,
            "risk_level": "HIGH",
            "top_factors": ["late_delivery"],
            "synthetic_data_flag": False,
            "model_version": "m1",
            "predicted_at": NOW,
            "data_source": "seller",
            "threshold_version": "t1",
            "aggregation_rule": "max",
        }
        order = {
            "order_id": order_id,
            "risk_score": 0.8,
            "risk_level": "HIGH",
            "status": "IN_PROGRESS",
            "assignee_id": str(SPECIALIST.id),
            "assignee_name": SPECIALIST.full_name,
            "queued_at": NOW,
            "original_queued_at": NOW,
            "sla_due_at": NOW,
            "matched_item_id": "item-1",
            "top_item": item,
            "top_factors": ["late_delivery"],
            "items_count": 1,
            "outcome": None,
            "skip_reason": None,
            "self_claim_allowed": False,
            "sla_state": "ON_TRACK",
            "sla_hours_left": 12.0,
            "aging_hours": 1.0,
            "total_aging_hours": 1.0,
            "is_escalated": False,
            "is_stale": False,
            "case_id": "case-1",
            "aggregation_rule": "max",
            "model_version": "m1",
            "predicted_at": NOW,
            "threshold_version": "t1",
            "seller_id": "seller-1",
            "category": "electronics",
            "cycle_no": 1,
            "updated_at": NOW,
            "closed_at": None,
            "reopen_count": 0,
            "contact_count": 1,
            "needs_decision": True,
            "has_synthetic_item": False,
            "items": [item],
        }
        payload = {
            "order": order,
            "cycles": [
                {
                    "cycle_no": 1,
                    "started_at": NOW,
                    "ended_at": None,
                    "sla_due_at": NOW,
                    "contact_count": 1,
                    "parameter_version": "p1",
                }
            ],
            "contacts": [{"contacted_at": NOW, "method": "PHONE", "result": "REACHED"}],
            "comments": [{"text": "comment"}],
            "decisions": [{"decision": "WORK_WITH_SELLER"}],
            "next_step": {"decision": "FOLLOW_UP"},
            "model_notes": [{"note": "note"}],
            "audit_events": [] if include_audit else None,
            "status_history": [
                {
                    "created_at": NOW,
                    "actor_name": "Boss",
                    "event_type": "ASSIGNED",
                    "old_value": None,
                    "new_value": "IN_PROGRESS",
                }
            ],
            "seller_open_count": 2,
        }
        if self.omit_collection:
            payload.pop(self.omit_collection)
        return payload

    def dashboard(self, now: datetime, **filters: Any) -> dict[str, Any]:
        return {"view": filters["view"], "days": filters["days"]}

    def audit_events(self, **filters: Any) -> dict[str, Any]:
        return {"items": [], "total": 0, "all_total": 0}


class FakeEvidence:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.saved: list[bytes] = []

    def save(self, owner_id: UUID, file_name: str | None, data: bytes) -> dict[str, Any]:
        if not data.startswith(b"\x89PNG"):
            raise WorkflowPolicyError("EVIDENCE_INVALID", "Evidence must be PNG, JPG or PDF")
        self.saved.append(data)
        return {"file_id": str(uuid4()), "file_name": file_name, "file_type": "image/png"}

    def locate(self, upload_id: UUID, user_id: UUID, is_manager: bool) -> tuple[Path, str, str]:
        if not is_manager:
            raise EvidenceAccessError(str(upload_id))
        return self.path, "image/png", "a.png"


@pytest.fixture
def ctx(tmp_path: Path) -> Any:
    commands, reads, evidence = FakeCommands(), FakeReads(), FakeEvidence(tmp_path / "a.png")
    (tmp_path / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    app = create_app(
        Settings(jwt_secret="x" * 20),
        auth=FakeAuth(),
        parameter_versions=object(),  # type: ignore[arg-type]
        risk_orders=object(),  # type: ignore[arg-type]
        operational_reads=object(),  # type: ignore[arg-type]
        claim_case=object(),  # type: ignore[arg-type]
        workflow_commands=commands,
        case_reads=reads,
        evidence_files=evidence,
    )
    return TestClient(app), commands, reads, evidence


def auth(role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {role}"}


def test_detail_hides_audit_from_specialist_and_shows_it_to_manager(ctx: Any) -> None:
    client, _, reads, _ = ctx
    assert (
        client.get("/api/v1/orders/abc", headers=auth("specialist")).json()["audit_events"] is None
    )
    assert reads.include_audit is False
    assert client.get("/api/v1/orders/abc", headers=auth("manager")).json()["audit_events"] == []
    assert reads.include_audit is True


def test_detail_serializes_complete_order_detail_and_rejects_missing_collection(ctx: Any) -> None:
    client, _, reads, _ = ctx
    response = client.get("/api/v1/orders/abc", headers=auth("manager"))
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "order",
        "cycles",
        "contacts",
        "comments",
        "decisions",
        "next_step",
        "model_notes",
        "audit_events",
        "status_history",
        "seller_open_count",
    }
    assert set(body["order"]) >= {"order_id", "top_item", "items", "status", "risk_score"}
    reads.omit_collection = "cycles"
    with pytest.raises(ValidationError):
        client.get("/api/v1/orders/abc", headers=auth("manager"))


def test_unknown_order_uses_the_error_envelope(ctx: Any) -> None:
    client, _, reads, _ = ctx
    reads.missing = True
    response = client.get("/api/v1/orders/abc", headers=auth("manager"))
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ORDER_NOT_FOUND"


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/assign", {"assignee_id": str(uuid4()), "reason": "r", "override_capacity": False}),
        ("/reopen", {"reason": "r", "review_confirmed": False}),
        ("/model-notes", {"note": "n"}),
        ("/decisions", {"decision": "NO_FURTHER_ACTION", "reason": "r", "next_step": "n"}),
    ],
)
def test_manager_only_writes_reject_specialists(ctx: Any, path: str, body: dict[str, Any]) -> None:
    client, commands, _, _ = ctx
    response = client.post(f"/api/v1/orders/abc{path}", json=body, headers=auth("specialist"))
    assert response.status_code == 403 and response.json()["error"]["code"] == "FORBIDDEN"
    assert commands.calls == []


@pytest.mark.parametrize(
    ("code", "http_status"),
    [
        ("REASON_REQUIRED", 422),
        ("CAPACITY_FULL", 422),
        ("MAX_CONTACTS_REACHED", 422),
        ("EVIDENCE_INVALID", 422),
        ("REVIEW_CONFIRMATION_REQUIRED", 422),
        ("INVALID_STATE", 409),
        ("FORBIDDEN", 403),
    ],
)
def test_policy_errors_map_to_contract_status_and_code(
    ctx: Any, code: str, http_status: int
) -> None:
    client, commands, _, _ = ctx
    commands.error = WorkflowPolicyError(code, "nope")
    response = client.post(
        "/api/v1/orders/abc/complete", json={"outcome": "HAS_ISSUE"}, headers=auth("manager")
    )
    assert response.status_code == http_status
    assert response.json()["error"]["code"] == code


def test_write_bodies_reject_unknown_fields(ctx: Any) -> None:
    client, commands, _, _ = ctx
    response = client.post(
        "/api/v1/orders/abc/skip", json={"reason": "OTHER", "bogus": 1}, headers=auth("manager")
    )
    assert response.status_code == 422 and commands.calls == []


def test_assign_returns_order_and_previous_assignee(ctx: Any) -> None:
    client, commands, _, _ = ctx
    body = {"assignee_id": str(uuid4()), "reason": "busy", "override_capacity": True}
    response = client.post("/api/v1/orders/abc/assign", json=body, headers=auth("manager"))
    assert response.status_code == 200
    assert response.json()["previous_assignee_name"] == "Old Holder"
    assert commands.calls[0][1][4] is True


def test_contact_requires_a_specialist_and_returns_contact_and_order(ctx: Any) -> None:
    client, commands, _, _ = ctx
    body = {"contacted_at": NOW.isoformat(), "method": "PHONE", "result": "REACHED"}
    assert (
        client.post("/api/v1/orders/abc/contacts", json=body, headers=auth("manager")).status_code
        == 403
    )
    response = client.post("/api/v1/orders/abc/contacts", json=body, headers=auth("specialist"))
    assert response.status_code == 201
    assert set(response.json()) == {"contact", "order"}
    assert commands.calls[-1][0] == "contact"


def test_decision_passes_all_fields_and_returns_201(ctx: Any) -> None:
    client, commands, _, _ = ctx
    body = {
        "decision": "WORK_WITH_SELLER",
        "reason": "r",
        "next_step": "n",
        "due_date": date(2030, 1, 1).isoformat(),
    }
    response = client.post("/api/v1/orders/abc/decisions", json=body, headers=auth("manager"))
    assert response.status_code == 201
    assert response.json()["decision"]["actor_name"] == "Boss"
    assert replace(commands.calls[0][1][0]).due_date == date(2030, 1, 1)


def test_upload_rejects_non_image_and_download_is_authorized(ctx: Any) -> None:
    client, _, _, evidence = ctx
    bad = client.post(
        "/api/v1/files", files={"file": ("x.png", b"MZ-not-an-image")}, headers=auth("specialist")
    )
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "EVIDENCE_INVALID"
    good = client.post(
        "/api/v1/files",
        files={"file": ("x.png", b"\x89PNG\r\n\x1a\nabc")},
        headers=auth("specialist"),
    )
    assert good.status_code == 201 and len(evidence.saved) == 1
    file_id = good.json()["file_id"]
    assert client.get(f"/api/v1/files/{file_id}", headers=auth("specialist")).status_code == 403
    assert client.get(f"/api/v1/files/{file_id}", headers=auth("manager")).status_code == 200


def test_dashboard_and_audit_are_manager_only_and_validate_query(ctx: Any) -> None:
    client, _, _, _ = ctx
    for path in ("/api/v1/dashboard", "/api/v1/audit-events"):
        assert client.get(path, headers=auth("specialist")).status_code == 403
    assert client.get("/api/v1/dashboard?days=5", headers=auth("manager")).status_code == 422
    assert client.get("/api/v1/dashboard?view=other", headers=auth("manager")).status_code == 422
    assert client.get("/api/v1/dashboard?days=7&view=product", headers=auth("manager")).json() == {
        "view": "product",
        "days": 7,
    }
    assert client.get("/api/v1/audit-events?limit=101", headers=auth("manager")).status_code == 422


def test_sanitize_file_name_drops_paths_and_unsafe_characters() -> None:
    assert sanitize_file_name("../../etc/pass wd.png") == "pass_wd.png"
    assert sanitize_file_name("C:\\Users\\x\\evil.pdf") == "evil.pdf"
    assert sanitize_file_name("") == "file"

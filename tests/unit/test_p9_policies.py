"""Branch coverage for the P9 domain/application policies not exercised elsewhere."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from hidden_dissatisfaction.application.auth import AuthService
from hidden_dissatisfaction.application.configuration import (
    GetEffectiveParameters,
    GetMLThresholds,
    GetUserWorkloadCapacity,
)
from hidden_dissatisfaction.application.queue_seeding import QueueSeeder, SeedSummary
from hidden_dissatisfaction.domain.auth import InvalidCredentials, InvalidToken, User, UserNotFound
from hidden_dissatisfaction.domain.case_metrics import MetricParameters, build_dashboard
from hidden_dissatisfaction.domain.configuration import (
    EffectiveParameterBundle,
    MLThresholds,
    WorkloadCapacity,
)
from hidden_dissatisfaction.domain.parameters import (
    ParameterValidationError,
    validate_parameter_change,
)
from hidden_dissatisfaction.domain.queue import QueueFilters, QueueQueryValidationError
from hidden_dissatisfaction.domain.workflow import (
    CaseSnapshot,
    WorkflowPolicyError,
    validate_claim,
    validate_close,
    validate_contact,
    validate_contact_inputs,
    validate_reopen,
)

NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)


def snap(**over: Any) -> CaseSnapshot:
    base = CaseSnapshot("IN_PROGRESS", "LOW", "u1", 0, 3, None, 0)
    return replace(base, **over)


def code_of(call: Any, *args: Any) -> str:
    with pytest.raises(WorkflowPolicyError) as err:
        call(*args)
    return str(err.value.code)


def test_claim_rejects_assigned_or_non_pending_cases_and_anonymous_actor() -> None:
    assert code_of(validate_claim, snap(status="IN_PROGRESS"), "u2", 0, 5) == "INVALID_STATE"
    assert code_of(validate_claim, snap(status="PENDING"), "u2", 0, 5) == "INVALID_STATE"
    assert (
        code_of(validate_claim, snap(status="PENDING", assignee_id=None), "", 0, 5) == "FORBIDDEN"
    )
    validate_claim(snap(status="PENDING", assignee_id=None), "u2", 4, 5)


@pytest.mark.parametrize(
    ("case", "outcome", "skip", "note", "code"),
    [
        (snap(status="PENDING"), "HAS_ISSUE", None, None, "INVALID_STATE"),
        (snap(), None, None, None, "VALIDATION_ERROR"),
        (snap(), "HAS_ISSUE", "REFUSED", None, "VALIDATION_ERROR"),
        (snap(), "UNREACHABLE", None, None, "VALIDATION_ERROR"),
        (snap(), None, "BOGUS", None, "VALIDATION_ERROR"),
        (snap(), None, "OTHER", "  ", "VALIDATION_ERROR"),
    ],
)
def test_close_rejections(
    case: CaseSnapshot, outcome: Any, skip: Any, note: Any, code: str
) -> None:
    assert code_of(validate_close, case, outcome, skip, note) == code


def test_close_accepts_every_legal_result() -> None:
    for outcome in ("HAS_ISSUE", "NO_ISSUE", "DUPLICATE"):
        validate_close(snap(), outcome, None, None)
    validate_close(snap(), None, "OTHER", "explained")
    validate_close(snap(), None, "REFUSED", None)


def test_contact_rejections_and_auto_skip_boundary() -> None:
    past = NOW - timedelta(minutes=1)
    assert (
        code_of(validate_contact, snap(status="PENDING"), past, NOW, "REACHED") == "INVALID_STATE"
    )
    assert code_of(validate_contact, snap(), NOW + timedelta(seconds=1), NOW, "REACHED") == (
        "VALIDATION_ERROR"
    )
    assert code_of(validate_contact, snap(), past.replace(tzinfo=None), NOW, "REACHED") == (
        "VALIDATION_ERROR"
    )
    assert code_of(validate_contact, snap(), past, NOW, "MAYBE") == "VALIDATION_ERROR"
    assert code_of(validate_contact, snap(contact_count=3), past, NOW, "REACHED") == (
        "MAX_CONTACTS_REACHED"
    )
    assert validate_contact(snap(contact_count=2), past, NOW, "NO_ANSWER") is True
    assert validate_contact(snap(contact_count=2), past, NOW, "REACHED") is False
    assert validate_contact(snap(contact_count=1), past, NOW, "NO_ANSWER") is False


def test_contact_inputs_reject_a_next_contact_before_the_contact() -> None:
    day = NOW.date()
    validate_contact_inputs("EMAIL", NOW, day, 0)
    assert code_of(validate_contact_inputs, "EMAIL", NOW, day - timedelta(days=1), 0) == (
        "VALIDATION_ERROR"
    )


def test_reopen_confirmation_thresholds() -> None:
    closed = snap(status="COMPLETED", closed_at=NOW - timedelta(days=3), reopen_count=0)
    validate_reopen(closed, NOW, 7, 2, False)
    assert code_of(validate_reopen, closed, NOW, 2, 2, False) == "REVIEW_CONFIRMATION_REQUIRED"
    assert code_of(validate_reopen, replace(closed, reopen_count=2), NOW, 7, 2, False) == (
        "REVIEW_CONFIRMATION_REQUIRED"
    )
    validate_reopen(replace(closed, reopen_count=2), NOW, 7, 2, True)
    assert code_of(validate_reopen, snap(status="IN_PROGRESS"), NOW, 7, 2, True) == "INVALID_STATE"
    assert code_of(validate_reopen, snap(status="COMPLETED"), NOW, 7, 2, True) == "INVALID_STATE"


def change(key: str, value: object, values: dict[str, str] | None = None) -> str:
    return validate_parameter_change(
        key=key,
        value=value,
        effective_at=NOW + timedelta(hours=1),
        reason="why",
        now=NOW,
        effective_values=values or {},
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("sla_calendar", "WEEKENDS"),
        ("sla_calendar", 3),
        ("capacity", "5"),
        ("capacity", True),
        ("capacity", 0),
        ("capacity", 21),
        ("nope", 1),
    ],
)
def test_parameter_value_rejections(key: str, value: object) -> None:
    with pytest.raises(ParameterValidationError) as err:
        change(key, value)
    assert err.value.code == "PARAMETER_INVALID"


def test_parameter_normalization_and_cross_rules() -> None:
    assert change("sla_calendar", "BUSINESS_HOURS") == "BUSINESS_HOURS"
    assert change("capacity", 6, {"capacity": "5", "capacity_warn": "4"}) == "6"
    with pytest.raises(ParameterValidationError):
        change("capacity_warn", 5, {"capacity": "5", "capacity_warn": "4"})
    with pytest.raises(ParameterValidationError) as err:
        change("capacity_warn", 3, {"capacity": "five"})
    assert err.value.code == "PARAMETER_INVALID"
    with pytest.raises(ParameterValidationError):
        validate_parameter_change(
            key="capacity",
            value=5,
            effective_at=NOW + timedelta(hours=1),
            reason="  ",
            now=NOW,
            effective_values={},
        )
    with pytest.raises(ParameterValidationError):
        validate_parameter_change(
            key="capacity",
            value=5,
            effective_at=NOW - timedelta(hours=1),
            reason="r",
            now=NOW,
            effective_values={},
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"level": "EXTREME"},
        {"status": "DONE"},
        {"sort": "random"},
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"score_min": 0.9, "score_max": 0.1},
        {"score_min": -0.1},
        {"score_max": 1.1},
        {"queued_from": NOW, "queued_to": NOW - timedelta(days=1)},
        {"sla": "late"},
        {"outcome": "O:BOGUS"},
        {"query": "XYZ"},
    ],
)
def test_queue_filter_rejections(kwargs: dict[str, Any]) -> None:
    with pytest.raises(QueueQueryValidationError):
        QueueFilters(**kwargs)


def test_queue_filter_accepts_every_documented_value() -> None:
    QueueFilters(
        query="a3f9",
        level="HIGH",
        status="OPEN",
        assignee="me",
        score_min=0.1,
        score_max=0.9,
        queued_from=NOW - timedelta(days=1),
        queued_to=NOW,
        seller="s",
        category="c",
        outcome="S:OTHER",
        sla="esc",
        needs_decision=True,
        sort="aging",
        limit=100,
        offset=0,
    )


class FakeReader:
    def effective_parameters(self, as_of: datetime) -> EffectiveParameterBundle:
        return EffectiveParameterBundle(3, as_of, {"capacity": "5"})

    def user_workload_capacity(self, user_id: Any) -> WorkloadCapacity:
        return WorkloadCapacity(str(user_id), 2, 5)

    def ml_thresholds(self, model_release_id: Any, threshold_version: str) -> MLThresholds:
        return MLThresholds(str(model_release_id), threshold_version, 0.4, 0.7)


def test_configuration_use_cases_delegate_to_the_reader() -> None:
    reader, user = FakeReader(), uuid4()
    assert GetEffectiveParameters(reader).execute(NOW).value("capacity") == "5"
    assert GetUserWorkloadCapacity(reader).execute(user).capacity == 5
    assert GetMLThresholds(reader).execute(user, "thr-1").high == 0.7


def test_queue_seeder_requires_a_prediction_and_delegates() -> None:
    class Store:
        def seed(self, prediction_id: str, now: datetime) -> SeedSummary:
            return SeedSummary(created=2, skipped=1)

    assert QueueSeeder(Store()).seed("run-1") == SeedSummary(2, 1)
    with pytest.raises(ValueError):
        QueueSeeder(Store()).seed("")


class Users:
    def __init__(self, user: User) -> None:
        self.user = user

    async def by_username(self, username: str) -> User | None:
        return self.user if username == self.user.username else None

    async def by_id(self, user_id: Any) -> User | None:
        return self.user if user_id == self.user.id else None

    async def set_preferred_language(self, user_id: Any, language: str) -> User:
        self.user = replace(self.user, preferred_language=language)
        return self.user


def test_auth_service_login_identify_and_language() -> None:
    service = AuthService(Users(User(uuid4(), "an", "x")), secret="s" * 32)
    hashed = service.passwords.hash("correct-password")
    user = replace(service.users.user, password_hash=hashed)  # type: ignore[attr-defined]
    service = AuthService(Users(user), secret="s" * 32)

    async def run() -> None:
        with pytest.raises(InvalidCredentials):
            await service.login("an", "wrong-password")
        with pytest.raises(InvalidCredentials):
            await service.login("nobody", "correct-password")
        token = await service.login("an", "correct-password")
        assert (await service.identify(token.token)).id == user.id
        with pytest.raises(InvalidToken):
            await service.identify("garbage")
        updated = await service.update_preferred_language(user, "en")
        assert updated.preferred_language == "en"
        with pytest.raises(UserNotFound):
            await service.update_preferred_language(replace(user, is_active=False), "vi")
        users = service.users
        users.user = replace(user, is_active=False)  # type: ignore[attr-defined]
        with pytest.raises(UserNotFound):
            await service.identify(token.token)

    asyncio.run(run())


def dash_row(order: str, **over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "order_id": order,
        "status": "IN_PROGRESS",
        "level": "LOW",
        "score": 0.3,
        "seller": None,
        "category": None,
        "assignee_id": "u1",
        "outcome": None,
        "original_queued_at": NOW - timedelta(days=5),
        "cycle_started_at": NOW - timedelta(days=5),
        "sla_due_at": NOW - timedelta(hours=1),
        "updated_at": NOW - timedelta(days=3),
        "contact_total": 0,
        "reached": False,
        "cycle_first_contact_at": None,
        "has_decision": False,
    }
    return {**base, **over}


def test_dashboard_rebalance_and_stale_actions() -> None:
    specialist = {
        "user_id": "u1",
        "full_name": "An",
        "active_count": 5,
        "capacity": 5,
        "slots_left": 0,
    }
    spare = {
        "user_id": "u2",
        "full_name": "Binh",
        "active_count": 1,
        "capacity": 5,
        "slots_left": 4,
    }
    out = build_dashboard(
        [dash_row("a")],
        [specialist, spare],
        [],
        now=NOW,
        params=MetricParameters(soon_hours=2, aging_days=2, stale_hours=24),
        since=None,
    )
    by_code = {a["code"]: a for a in out["actions"]}
    assert by_code["REBALANCE"]["suggest"] == "Binh" and by_code["REBALANCE"]["overdue"] == 1
    assert by_code["STALE"]["count"] == 1 and by_code["STALE"]["hours"] == 24
    assert out["workload"][0]["overdue"] == 1 and out["workload"][1]["overdue"] == 0
    assert out["by_seller"][0]["key"] == "unknown" and "SELLER_HOTSPOT" not in by_code


def test_assign_rejects_reassigning_to_the_current_holder() -> None:
    from hidden_dissatisfaction.domain.workflow import validate_assign

    assert (
        code_of(validate_assign, "IN_PROGRESS", "u1", "u1", "why", 0, 5, False) == "INVALID_STATE"
    )

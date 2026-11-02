"""DSN-gated integration coverage for the P9 write workflow on a migrated PostgreSQL."""

import os
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import psycopg
import pytest

from hidden_dissatisfaction.application.workflow_commands import (
    AddContact,
    AddDecision,
    EvidenceRef,
)
from hidden_dissatisfaction.domain.queue import QueueFilters
from hidden_dissatisfaction.domain.workflow import WorkflowPolicyError
from hidden_dissatisfaction.infrastructure.postgres_claim_case import (
    ClaimConflictError,
    PostgresClaimCase,
)
from hidden_dissatisfaction.infrastructure.postgres_workflow_commands import (
    PostgresWorkflowCommands,
)

SETUP_DSN = os.environ.get("P9_TEST_POSTGRES_DSN")
RUNTIME_DSN = os.environ.get("P9_APP_RUNTIME_DSN")
pytestmark = pytest.mark.integration
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 8


@pytest.fixture
def db() -> Any:
    if not SETUP_DSN or not RUNTIME_DSN:
        pytest.skip("P9_TEST_POSTGRES_DSN and P9_APP_RUNTIME_DSN are required")
    with psycopg.connect(SETUP_DSN, autocommit=True) as conn:
        yield conn


@pytest.fixture
def prediction_id(db: psycopg.Connection[Any]) -> str:
    row = db.execute("SELECT prediction_id FROM ml.predictions WHERE state='ACTIVE'").fetchone()
    if row:
        return str(row[0])
    release, pid = uuid4(), uuid4()
    db.execute(
        """INSERT INTO ml.model_releases(model_release_id, release_version, model_name, model_version,
           model_artifact_uri, artifact_sha256, feature_schema_version, dataset_manifest_sha256,
           training_git_sha, source_snapshot_hash, training_run_id, aggregation_rule, evaluation_status)
           VALUES (%s,%s,'it','1','urn:it',%s,'gold-v1',%s,%s,%s,%s,'max-v1','CONFIRMATORY')""",
        (release, f"wf-it-{release.hex[:8]}", "a" * 64, "b" * 64, "c" * 64, "d" * 64, uuid4()),
    )
    db.execute(
        "INSERT INTO ml.model_thresholds(model_release_id, threshold_version, medium_from, high_from) "
        "VALUES (%s,'it-1',.5,.8)",
        (release,),
    )
    db.execute(
        """INSERT INTO ml.predictions(prediction_id, model_release_id, threshold_version, source_run_id,
           input_hash, model_input_hash, scored_at, state)
           VALUES (%s,%s,'it-1',%s,%s,%s,now(),'ACTIVE')""",
        (pid, release, uuid4(), "e" * 64, "f" * 64),
    )
    return str(pid)


def _user(db: psycopg.Connection[Any], role: str) -> UUID:
    user_id = uuid4()
    db.execute(
        "INSERT INTO app.users(user_id, username, password_hash, full_name, role) "
        "VALUES (%s,%s,'x',%s,%s)",
        (user_id, f"{role.lower()}-{user_id.hex[:10]}", f"{role} {user_id.hex[:4]}", role),
    )
    return user_id


@pytest.fixture
def make_case(db: psycopg.Connection[Any], prediction_id: str) -> Callable[..., str]:
    def make(score: float = 0.0, assignee: UUID | None = None, status: str | None = None) -> str:
        order_id = uuid4().hex
        item = f"{order_id}-1"
        db.execute(
            "INSERT INTO ml.item_prediction_scores(prediction_id, order_id, order_item_id, "
            "product_item_id, score) VALUES (%s,%s,'1',%s,%s)",
            (prediction_id, order_id, item, score),
        )
        db.execute(
            "INSERT INTO ml.order_prediction_scores(prediction_id, order_id, score, aggregation_rule, "
            "top_product_item_id, top_item_score, item_count, item_value) "
            "VALUES (%s,%s,%s,'max-v1',%s,%s,1,10)",
            (prediction_id, order_id, score, item, score),
        )
        case = db.execute(
            "INSERT INTO app.review_cases(order_id, prediction_id, aggregation_rule, status, assignee_id) "
            "VALUES (%s,%s,'max-v1',%s,%s) RETURNING case_id",
            (
                order_id,
                prediction_id,
                status or ("IN_PROGRESS" if assignee else "PENDING"),
                assignee,
            ),
        ).fetchone()
        assert case is not None
        db.execute(
            "INSERT INTO app.review_cycles(case_id, cycle_no, started_at, sla_due_at) "
            "VALUES (%s,1,now(),now()+interval '4 hours')",
            (case[0],),
        )
        if assignee:
            db.execute(
                "INSERT INTO app.assignments(case_id, assignee_id) VALUES (%s,%s)",
                (case[0], assignee),
            )
        return order_id

    return make


def _commands() -> PostgresWorkflowCommands:
    assert RUNTIME_DSN
    return PostgresWorkflowCommands(RUNTIME_DSN)


def _contact(order_id: str, actor: UUID, result: str, files: tuple[UUID, ...] = ()) -> AddContact:
    return AddContact(
        order_id,
        actor,
        datetime.now(UTC) - timedelta(minutes=1),
        "PHONE",
        result,
        "n",
        None,
        None,
        tuple(EvidenceRef(f) for f in files),
    )


def _scalar(db: psycopg.Connection[Any], sql: str, *args: object) -> Any:
    row = db.execute(sql, args).fetchone()
    assert row is not None
    return row[0]


def _upload(db: psycopg.Connection[Any], owner: UUID) -> UUID:
    row = db.execute(
        "INSERT INTO app.evidence_uploads(uploaded_by, storage_key, file_name, content_type, file_size) "
        "VALUES (%s,%s,'a.png','image/png',16) RETURNING upload_id",
        (owner, f"it/{uuid4()}.png"),
    ).fetchone()
    assert row is not None
    return UUID(str(row[0]))


def test_two_specialists_claim_one_case_exactly_one_wins(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    assert RUNTIME_DSN
    first, second, order_id = _user(db, "SPECIALIST"), _user(db, "SPECIALIST"), make_case()
    claim = PostgresClaimCase(RUNTIME_DSN)

    def attempt(actor: UUID) -> str:
        try:
            claim.execute(order_id, actor)
            return "won"
        except (ClaimConflictError, WorkflowPolicyError) as exc:
            return getattr(exc, "code", "ALREADY_CLAIMED")

    with ThreadPoolExecutor(2) as pool:
        results = sorted(pool.map(attempt, [first, second]))
    assert results.count("won") == 1
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.assignments a JOIN app.review_cases c USING (case_id) "
            "WHERE c.order_id=%s AND a.released_at IS NULL",
            order_id,
        )
        == 1
    )


def test_final_unsuccessful_attempt_auto_skips_atomically(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    specialist, order_id = _user(db, "SPECIALIST"), make_case(assignee=None)
    manager = _user(db, "MANAGER")
    commands = _commands()
    commands.assign(order_id, manager, specialist, None, False)
    assert commands.add_contact(_contact(order_id, specialist, "NO_ANSWER")).auto_skipped is False
    assert commands.add_contact(_contact(order_id, specialist, "CALLBACK")).auto_skipped is False
    last = commands.add_contact(_contact(order_id, specialist, "NO_ANSWER"))
    assert (last.attempt_no, last.auto_skipped) == (3, True)
    status, reason, assignee = (
        db.execute(
            "SELECT status, skip_reason, assignee_id FROM app.review_cases WHERE order_id=%s",
            (order_id,),
        ).fetchone()
        or (None,) * 3
    )
    assert (status, reason) == ("SKIPPED", "UNREACHABLE")
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.assignments a JOIN app.review_cases c USING (case_id) "
            "WHERE c.order_id=%s AND a.released_at IS NULL",
            order_id,
        )
        == 0
    )
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.review_cycles r JOIN app.review_cases c USING (case_id) "
            "WHERE c.order_id=%s AND r.ended_at IS NULL",
            order_id,
        )
        == 0
    )
    events = [
        r[0]
        for r in db.execute(
            "SELECT event_type FROM app.audit_events WHERE order_id=%s ORDER BY event_id",
            (order_id,),
        )
    ]
    assert events.count("CONTACT") == 3 and events[-1] == "SKIP"
    with pytest.raises(WorkflowPolicyError):
        commands.add_contact(_contact(order_id, specialist, "NO_ANSWER"))


def test_rejected_evidence_rolls_back_the_whole_attempt(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    specialist, other = _user(db, "SPECIALIST"), _user(db, "SPECIALIST")
    order_id = make_case(assignee=specialist)
    foreign = _upload(db, other)
    with pytest.raises(WorkflowPolicyError) as err:
        _commands().add_contact(_contact(order_id, specialist, "REACHED", (foreign,)))
    assert err.value.code == "EVIDENCE_INVALID"
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.contact_attempts a JOIN app.review_cases c "
            "USING (case_id) WHERE c.order_id=%s",
            order_id,
        )
        == 0
    )
    assert _scalar(db, "SELECT count(*) FROM app.audit_events WHERE order_id=%s", order_id) == 0


def test_evidence_attaches_once_and_cannot_be_reused(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    specialist = _user(db, "SPECIALIST")
    first, second = make_case(assignee=specialist), make_case(assignee=specialist)
    file_id = _upload(db, specialist)
    _commands().add_contact(_contact(first, specialist, "REACHED", (file_id,)))
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.contact_evidence e JOIN app.review_cases c "
            "USING (case_id) WHERE c.order_id=%s",
            first,
        )
        == 1
    )
    with pytest.raises(WorkflowPolicyError) as err:
        _commands().add_contact(_contact(second, specialist, "REACHED", (file_id,)))
    assert err.value.code == "EVIDENCE_INVALID"


def test_only_current_assignee_may_add_contacts(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    holder, intruder = _user(db, "SPECIALIST"), _user(db, "SPECIALIST")
    order_id = make_case(assignee=holder)
    with pytest.raises(WorkflowPolicyError) as err:
        _commands().add_contact(_contact(order_id, intruder, "REACHED"))
    assert err.value.code == "FORBIDDEN"


def test_runtime_role_cannot_update_or_delete_append_only_tables(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    assert RUNTIME_DSN
    specialist = _user(db, "SPECIALIST")
    order_id = make_case(assignee=specialist)
    _commands().add_contact(_contact(order_id, specialist, "REACHED"))
    with psycopg.connect(RUNTIME_DSN, autocommit=True) as runtime:
        for sql in (
            "UPDATE app.contact_attempts SET note='x'",
            "DELETE FROM app.contact_attempts",
            "UPDATE app.audit_events SET reason='x'",
            "DELETE FROM app.manager_decisions",
        ):
            with pytest.raises(psycopg.Error):
                runtime.execute(sql)


def test_reassign_and_capacity_override_are_audited(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    manager, first, second = _user(db, "MANAGER"), _user(db, "SPECIALIST"), _user(db, "SPECIALIST")
    capacity = int(
        _scalar(
            db,
            "SELECT value FROM app.parameters WHERE param_key='capacity' AND effective_at <= now() "
            "ORDER BY effective_at DESC, version DESC LIMIT 1",
        )
    )
    for _ in range(capacity):
        make_case(assignee=second)
    order_id = make_case(assignee=first)
    commands = _commands()
    with pytest.raises(WorkflowPolicyError) as no_reason:
        commands.assign(order_id, manager, second, "", False)
    assert no_reason.value.code == "REASON_REQUIRED"
    with pytest.raises(WorkflowPolicyError) as full:
        commands.assign(order_id, manager, second, "rebalance", False)
    assert full.value.code == "CAPACITY_FULL"
    result = commands.assign(order_id, manager, second, "rebalance", True)
    assert result.previous_assignee_name is not None
    events = [
        r[0]
        for r in db.execute(
            "SELECT event_type FROM app.audit_events WHERE order_id=%s ORDER BY event_id",
            (order_id,),
        )
    ]
    assert events == ["REASSIGN", "OVERRIDE"]
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.assignments a JOIN app.review_cases c USING (case_id) "
            "WHERE c.order_id=%s AND a.released_at IS NULL",
            order_id,
        )
        == 1
    )


def test_complete_then_reopen_starts_a_new_cycle_and_keeps_history(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    manager, specialist = _user(db, "MANAGER"), _user(db, "SPECIALIST")
    order_id = make_case(assignee=specialist)
    commands = _commands()
    queued = _scalar(
        db, "SELECT original_queued_at FROM app.review_cases WHERE order_id=%s", order_id
    )
    commands.add_contact(_contact(order_id, specialist, "REACHED"))
    commands.complete(order_id, specialist, False, "HAS_ISSUE", "found")
    with pytest.raises(WorkflowPolicyError) as err:
        commands.reopen(order_id, manager, " ", False)
    assert err.value.code == "REASON_REQUIRED"
    commands.reopen(order_id, manager, "customer called again", False)
    status, assignee, cycle_no, reopened, original = (
        db.execute(
            "SELECT status, assignee_id, cycle_no, reopen_count, original_queued_at "
            "FROM app.review_cases WHERE order_id=%s",
            (order_id,),
        ).fetchone()
        or (None,) * 5
    )
    assert (status, assignee, cycle_no, reopened, original) == ("PENDING", None, 2, 1, queued)
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.contact_attempts a JOIN app.review_cases c "
            "USING (case_id) WHERE c.order_id=%s",
            order_id,
        )
        == 1
    )


def test_decision_is_appended_to_the_current_cycle_without_changing_status(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    manager, specialist = _user(db, "MANAGER"), _user(db, "SPECIALIST")
    order_id = make_case(assignee=specialist)
    commands = _commands()
    commands.complete(order_id, manager, True, "NO_ISSUE", None)
    saved = commands.add_decision(
        AddDecision(
            order_id,
            manager,
            "FOLLOW_UP_CUSTOMER",
            "warranty",
            "call back",
            specialist,
            datetime.now(UTC).date(),
            None,
        )
    )
    assert saved["cycle_no"] == 1
    assert (
        _scalar(db, "SELECT status FROM app.review_cases WHERE order_id=%s", order_id)
        == "COMPLETED"
    )
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.audit_events WHERE order_id=%s AND " "event_type='DECISION'",
            order_id,
        )
        == 1
    )
    with pytest.raises(WorkflowPolicyError):
        commands.add_decision(
            AddDecision(order_id, manager, "FOLLOW_UP_CUSTOMER", "r", "n", uuid4(), None, None)
        )


def _reads() -> Any:
    from hidden_dissatisfaction.infrastructure.postgres_case_reads import PostgresCaseReads

    assert RUNTIME_DSN
    return PostgresCaseReads(RUNTIME_DSN)


def test_detail_projects_cycles_contacts_decisions_and_role_based_audit(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    manager, specialist = _user(db, "MANAGER"), _user(db, "SPECIALIST")
    order_id = make_case(assignee=specialist)
    commands, reads = _commands(), _reads()
    file_id = _upload(db, specialist)
    commands.add_contact(_contact(order_id, specialist, "REACHED", (file_id,)))
    commands.add_comment(order_id, specialist, False, "called")
    commands.complete(order_id, specialist, False, "HAS_ISSUE", None)
    commands.add_decision(
        AddDecision(order_id, manager, "WORK_WITH_SELLER", "r", "n", None, None, None)
    )
    now = datetime.now(UTC)
    as_specialist = reads.detail(order_id, now, include_audit=False)
    as_manager = reads.detail(order_id, now, include_audit=True)
    assert as_specialist["audit_events"] is None and len(as_manager["audit_events"]) >= 4
    order = as_manager["order"]
    assert (order["status"], order["needs_decision"], order["sla_state"]) == (
        "COMPLETED",
        False,
        "none",
    )
    assert order["items_count"] == 1 and order["top_item"]["product_item_id"].endswith("-1")
    assert order["top_item"]["threshold_version"] == "1"
    assert order["top_item"]["aggregation_rule"] == "max-v1"
    assert as_manager["next_step"]["decision"] == "WORK_WITH_SELLER"
    contact = as_manager["contacts"][0]
    assert contact["attempt_no"] == 1 and contact["evidence"][0]["file_id"] == str(file_id)
    assert [c["text"] for c in as_manager["comments"]] == ["called"]
    assert len(as_manager["cycles"]) == 1 and as_manager["cycles"][0]["contact_count"] == 1


def test_dashboard_reconciles_with_queue_filters_and_supports_product_view(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    make_case(score=0.95), make_case(score=0.1)
    reads = _reads()
    now = datetime.now(UTC)
    kwargs: dict[str, Any] = {
        "days": None,
        "level": None,
        "seller": None,
        "category": None,
        "assignee": None,
        "status": "OPEN",
        "product_item": None,
        "view": "order",
    }
    by_order = reads.dashboard(now, **kwargs)
    open_total = _scalar(
        db, "SELECT count(*) FROM app.review_cases WHERE status IN ('PENDING','IN_PROGRESS')"
    )
    assert by_order["totals"]["cases"] == open_total
    assert sum(by_order["by_level"].values()) == open_total
    assert sum(d["HIGH"] + d["MEDIUM"] + d["LOW"] for d in by_order["trend"]) == open_total
    product = reads.dashboard(now, **{**kwargs, "view": "product"})
    assert product["product"]["totals"]["orders"] == open_total
    assert product["product"]["totals"]["total_items"] >= open_total


def test_queue_can_project_closed_cases_awaiting_manager_decision(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    from hidden_dissatisfaction.infrastructure.postgres_risk_queue import PostgresRiskOrderQuery

    specialist = _user(db, "SPECIALIST")
    order_id = make_case(assignee=specialist)
    _commands().complete(order_id, specialist, False, "HAS_ISSUE", None)

    page = PostgresRiskOrderQuery(RUNTIME_DSN or "").list_orders(
        QueueFilters(status="COMPLETED", needs_decision=True)
    )

    projected = next(item for item in page.items if item.order_id == order_id)
    assert projected.queued_at is not None
    assert projected.status == "COMPLETED"


def test_audit_events_are_filtered_paginated_and_counted(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    manager, specialist = _user(db, "MANAGER"), _user(db, "SPECIALIST")
    order_id = make_case()
    _commands().assign(order_id, manager, specialist, None, False)
    page = _reads().audit_events(
        event_type="ASSIGN",
        actor_id=None,
        order_id=order_id[:12],
        override_only=False,
        limit=1,
        offset=0,
    )
    assert page["total"] == 1 and page["all_total"] >= 1
    assert page["items"][0]["order"]["assignee_name"] is not None
    none = _reads().audit_events(
        event_type=None, actor_id=None, order_id=order_id, override_only=True, limit=20, offset=0
    )
    assert none["total"] == 0


def _set_sla_hours(db: psycopg.Connection[Any], manager: UUID, hours: int) -> datetime:
    """Insert an already-effective SLA version directly (the writer forbids past times)."""
    version = _scalar(
        db, "SELECT coalesce(max(version),0)+1 FROM app.parameters WHERE param_key='sla_hours_low'"
    )
    effective = datetime.now(UTC)
    db.execute(
        "INSERT INTO app.parameters(param_key, version, value, effective_at, actor_id, reason) "
        "VALUES ('sla_hours_low', %s, %s, %s, %s, 'it')",
        (version, str(hours), effective, manager),
    )
    return effective


def test_sla_recalculation_updates_open_cycles_only_and_is_idempotent(
    db: psycopg.Connection[Any], make_case: Callable[..., str]
) -> None:
    from hidden_dissatisfaction.infrastructure.postgres_risk_queue import PostgresRiskOrderQuery
    from hidden_dissatisfaction.infrastructure.sla_recalculation import PostgresSlaRecalculator

    assert RUNTIME_DSN
    manager, specialist = _user(db, "MANAGER"), _user(db, "SPECIALIST")
    open_id, closed_id = make_case(assignee=specialist), make_case(assignee=specialist)
    _commands().complete(closed_id, specialist, False, "NO_ISSUE", None)
    original = _scalar(
        db,
        "SELECT sla_due_at FROM app.review_cycles y JOIN app.review_cases c "
        "USING (case_id) WHERE c.order_id=%s",
        open_id,
    )
    effective = _set_sla_hours(db, manager, 10)
    recalculator = PostgresSlaRecalculator(RUNTIME_DSN)
    later = effective + timedelta(seconds=1)
    assert recalculator.run(later) >= 1
    assert recalculator.run(later) == 0  # idempotent

    due = (
        PostgresRiskOrderQuery(RUNTIME_DSN)
        .list_orders(QueueFilters(query=open_id[:20], limit=5))
        .items[0]
        .sla_due_at
    )
    started = _scalar(
        db,
        "SELECT started_at FROM app.review_cycles y JOIN app.review_cases c "
        "USING (case_id) WHERE c.order_id=%s",
        open_id,
    )
    assert due == started + timedelta(hours=10) and due != original
    # history untouched: the stored cycle value and the closed case's cycle never change
    assert (
        _scalar(
            db,
            "SELECT sla_due_at FROM app.review_cycles y JOIN app.review_cases c "
            "USING (case_id) WHERE c.order_id=%s",
            open_id,
        )
        == original
    )
    assert (
        _scalar(
            db,
            "SELECT count(*) FROM app.sla_adjustments a JOIN app.review_cycles y "
            "USING (cycle_id) JOIN app.review_cases c USING (case_id) "
            "WHERE c.order_id=%s",
            closed_id,
        )
        == 0
    )


def test_purge_removes_only_expired_unattached_uploads(
    db: psycopg.Connection[Any], make_case: Callable[..., str], tmp_path: Any
) -> None:
    from hidden_dissatisfaction.infrastructure.evidence_cleanup import purge_unattached_uploads

    assert RUNTIME_DSN
    tag = uuid4().hex[:8]
    specialist = _user(db, "SPECIALIST")
    order_id = make_case(assignee=specialist)
    old, kept = _upload(db, specialist), _upload(db, specialist)
    attached = _upload(db, specialist)
    _commands().add_contact(_contact(order_id, specialist, "REACHED", (attached,)))
    db.execute("ALTER TABLE app.evidence_uploads DISABLE TRIGGER evidence_uploads_guard")
    try:
        for upload_id, key in (
            (old, f"{tag}-old.png"),
            (kept, f"{tag}-kept.png"),
            (attached, f"{tag}-attached.png"),
        ):
            (tmp_path / key).write_bytes(PNG)
            db.execute(
                "UPDATE app.evidence_uploads SET storage_key=%s WHERE upload_id=%s",
                (key, upload_id),
            )
        db.execute(
            "UPDATE app.evidence_uploads SET uploaded_at = now() - interval '2 days' "
            "WHERE upload_id IN (%s, %s)",
            (old, attached),
        )
    finally:
        db.execute("ALTER TABLE app.evidence_uploads ENABLE TRIGGER evidence_uploads_guard")
    assert purge_unattached_uploads(RUNTIME_DSN, tmp_path, datetime.now(UTC)) >= 1
    remaining = {
        r[0]
        for r in db.execute(
            "SELECT upload_id FROM app.evidence_uploads WHERE upload_id IN (%s,%s,%s)",
            (old, kept, attached),
        )
    }
    assert remaining == {kept, attached}
    assert not (tmp_path / f"{tag}-old.png").exists()
    assert (tmp_path / f"{tag}-attached.png").exists()
    with psycopg.connect(RUNTIME_DSN, autocommit=True) as runtime, pytest.raises(psycopg.Error):
        runtime.execute("DELETE FROM app.evidence_uploads WHERE upload_id=%s", (attached,))

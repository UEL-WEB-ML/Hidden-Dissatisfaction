"""Transactional PostgreSQL adapter for the P9 case workflow write use cases."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from hidden_dissatisfaction.application.workflow_commands import (
    AddContact,
    AddDecision,
    AssignResult,
    ContactResult,
)
from hidden_dissatisfaction.domain.workflow import (
    CaseNotFoundError,
    CaseSnapshot,
    WorkflowPolicyError,
    require_reason,
    validate_assign,
    validate_close,
    validate_comment,
    validate_contact,
    validate_contact_inputs,
    validate_decision,
    validate_reopen,
)

_CHANNEL = {"PHONE": "PHONE", "EMAIL": "EMAIL", "MESSAGE": "CHAT"}
_Conn = psycopg.Connection[Any]
_CONCURRENT = ("INVALID_STATE", "The case changed concurrently")


def _param(conn: _Conn, key: str, now: datetime) -> int:
    row = conn.execute(
        """SELECT value FROM app.parameters WHERE param_key=%s AND effective_at<=%s
           ORDER BY effective_at DESC, version DESC LIMIT 1""",
        (key, now),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"No effective parameter {key}")
    return int(row["value"])


class PostgresWorkflowCommands:
    """One database transaction per method; every write also appends its audit event."""

    def __init__(self, dsn: str, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._dsn = dsn
        self._clock = clock

    def _connect(self) -> _Conn:
        return psycopg.connect(self._dsn, row_factory=dict_row)

    @staticmethod
    def _lock_case(conn: _Conn, order_id: str) -> dict[str, Any]:
        row = conn.execute(
            """SELECT c.case_id, c.status, c.assignee_id, c.row_version, c.cycle_no, c.closed_at,
                      c.reopen_count, r.risk_level
               FROM app.review_cases c
               JOIN ml.v_risk_orders_for_web r
                 ON r.prediction_id=c.prediction_id AND r.order_id=c.order_id
               WHERE c.order_id=%s FOR UPDATE OF c""",
            (order_id,),
        ).fetchone()
        if row is None:
            raise CaseNotFoundError(order_id)
        return dict(row)

    @staticmethod
    def _audit(
        conn: _Conn,
        case: dict[str, Any],
        order_id: str,
        actor_id: UUID,
        event_type: str,
        old: str | None,
        new: str,
        reason: str | None = None,
    ) -> None:
        conn.execute(
            """INSERT INTO app.audit_events(case_id, order_id, actor_id, provenance, event_type,
                                            old_value, new_value, reason)
               VALUES (%s,%s,%s,'USER',%s,%s,%s,%s)""",
            (case["case_id"], order_id, actor_id, event_type, old, new, reason),
        )

    @staticmethod
    def _bump(conn: _Conn, case: dict[str, Any], now: datetime) -> None:
        updated = conn.execute(
            "UPDATE app.review_cases SET updated_at=%s, row_version=row_version+1 "
            "WHERE case_id=%s AND row_version=%s",
            (now, case["case_id"], case["row_version"]),
        )
        if updated.rowcount != 1:
            raise WorkflowPolicyError(*_CONCURRENT)

    @staticmethod
    def _open_cycle(conn: _Conn, case_id: object) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT cycle_id, cycle_no, started_at FROM app.review_cycles "
            "WHERE case_id=%s AND ended_at IS NULL",
            (case_id,),
        ).fetchone()
        return dict(row) if row else None

    def _close(
        self,
        conn: _Conn,
        case: dict[str, Any],
        status: str,
        outcome: str | None,
        skip_reason: str | None,
        note: str | None,
        now: datetime,
    ) -> None:
        updated = conn.execute(
            """UPDATE app.review_cases SET status=%s, outcome=%s, skip_reason=%s, close_note=%s,
                      closed_at=%s, updated_at=%s, row_version=row_version+1
               WHERE case_id=%s AND row_version=%s""",
            (status, outcome, skip_reason, note, now, now, case["case_id"], case["row_version"]),
        )
        if updated.rowcount != 1:
            raise WorkflowPolicyError(*_CONCURRENT)
        conn.execute(
            "UPDATE app.assignments SET released_at=%s, release_reason=%s "
            "WHERE case_id=%s AND released_at IS NULL",
            (now, status, case["case_id"]),
        )
        cycle = self._open_cycle(conn, case["case_id"])
        if cycle is not None:
            conn.execute("SELECT app.close_review_cycle(%s, %s)", (cycle["cycle_id"], now))

    def assign(
        self,
        order_id: str,
        actor_id: UUID,
        assignee_id: UUID,
        reason: str | None,
        override_capacity: bool,
    ) -> AssignResult:
        """Manager assign or reassign; releases the old assignment in the same transaction."""
        now = self._clock()
        with self._connect() as conn, conn.transaction():
            case = self._lock_case(conn, order_id)
            target = conn.execute(
                "SELECT full_name FROM app.users WHERE user_id=%s AND is_active AND role='SPECIALIST'",
                (assignee_id,),
            ).fetchone()
            if target is None:
                raise WorkflowPolicyError(
                    "VALIDATION_ERROR", "assignee_id must be an active Specialist"
                )
            conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (str(assignee_id),))
            active = conn.execute(
                "SELECT count(*)::int AS n FROM app.assignments "
                "WHERE assignee_id=%s AND released_at IS NULL",
                (assignee_id,),
            ).fetchone()
            if active is None:
                raise RuntimeError("Workload query returned no row")
            held = int(active["n"])
            capacity = _param(conn, "capacity", now)
            previous = case["assignee_id"]
            overridden = validate_assign(
                case["status"],
                str(previous) if previous else None,
                str(assignee_id),
                reason,
                held,
                capacity,
                override_capacity,
            )
            previous_name = None
            if previous is not None:
                row = conn.execute(
                    "SELECT full_name FROM app.users WHERE user_id=%s", (previous,)
                ).fetchone()
                previous_name = row["full_name"] if row else None
                conn.execute(
                    "UPDATE app.assignments SET released_at=%s, release_reason=%s "
                    "WHERE case_id=%s AND released_at IS NULL",
                    (now, require_reason(reason), case["case_id"]),
                )
            conn.execute(
                "INSERT INTO app.assignments(case_id, assignee_id, assigned_at) VALUES (%s,%s,%s)",
                (case["case_id"], assignee_id, now),
            )
            updated = conn.execute(
                """UPDATE app.review_cases SET status='IN_PROGRESS', assignee_id=%s, updated_at=%s,
                          row_version=row_version+1 WHERE case_id=%s AND row_version=%s""",
                (assignee_id, now, case["case_id"], case["row_version"]),
            )
            if updated.rowcount != 1:
                raise WorkflowPolicyError(*_CONCURRENT)
            clean_reason = (reason or "").strip() or None
            self._audit(
                conn,
                case,
                order_id,
                actor_id,
                "REASSIGN" if previous else "ASSIGN",
                f"{case['status']} · {previous_name or '(none)'}",
                f"IN_PROGRESS · {target['full_name']}",
                clean_reason,
            )
            if overridden:
                self._audit(
                    conn,
                    case,
                    order_id,
                    actor_id,
                    "OVERRIDE",
                    f"{held}/{capacity}",
                    f"{held + 1}/{capacity}",
                    clean_reason,
                )
            return AssignResult(previous_name)

    def _close_by_holder(
        self,
        order_id: str,
        actor_id: UUID,
        is_manager: bool,
        outcome: str | None,
        skip_reason: str | None,
        note: str | None,
    ) -> None:
        now = self._clock()
        with self._connect() as conn, conn.transaction():
            case = self._lock_case(conn, order_id)
            if not is_manager and case["assignee_id"] != actor_id:
                raise WorkflowPolicyError("FORBIDDEN", "Only the assignee or a Manager may close")
            validate_close(
                CaseSnapshot(case["status"], case["risk_level"], None, 0, 0, None, 0),
                outcome,
                skip_reason,
                note,
            )
            status = "COMPLETED" if outcome else "SKIPPED"
            clean_note = (note or "").strip() or None
            self._close(conn, case, status, outcome, skip_reason, clean_note, now)
            self._audit(
                conn,
                case,
                order_id,
                actor_id,
                "STATUS" if outcome else "SKIP",
                "IN_PROGRESS",
                f"{status} · {outcome or skip_reason}",
                clean_note,
            )

    def complete(
        self, order_id: str, actor_id: UUID, is_manager: bool, outcome: str, note: str | None
    ) -> None:
        """Close an in-progress case with a valid outcome."""
        self._close_by_holder(order_id, actor_id, is_manager, outcome, None, note)

    def skip(
        self, order_id: str, actor_id: UUID, is_manager: bool, reason: str, note: str | None
    ) -> None:
        """Skip an in-progress case with a valid reason."""
        self._close_by_holder(order_id, actor_id, is_manager, None, reason, note)

    def reopen(
        self, order_id: str, actor_id: UUID, reason: str | None, review_confirmed: bool
    ) -> None:
        """Start a new review cycle; history and ``original_queued_at`` stay untouched."""
        now = self._clock()
        with self._connect() as conn, conn.transaction():
            case = self._lock_case(conn, order_id)
            validate_reopen(
                CaseSnapshot(
                    case["status"],
                    case["risk_level"],
                    None,
                    0,
                    0,
                    case["closed_at"],
                    int(case["reopen_count"]),
                ),
                now,
                _param(conn, "reopen_review_days", now),
                _param(conn, "reopen_review_times", now),
                review_confirmed,
            )
            clean_reason = require_reason(reason)
            revision = conn.execute(
                """SELECT max(b.revision) AS r FROM app.parameter_bundles b
                   JOIN app.parameters p ON p.parameter_id=b.parameter_id
                   WHERE p.effective_at<=%s""",
                (now,),
            ).fetchone()
            sla_hours = _param(conn, f"sla_hours_{str(case['risk_level']).lower()}", now)
            cycle_no = int(case["cycle_no"]) + 1
            conn.execute(
                """INSERT INTO app.review_cycles(case_id, cycle_no, started_at, sla_due_at,
                          reopen_reason, reopened_by, parameter_version)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (
                    case["case_id"],
                    cycle_no,
                    now,
                    now + timedelta(hours=sla_hours),
                    clean_reason,
                    actor_id,
                    f"bundle-{revision['r']}" if revision and revision["r"] else None,
                ),
            )
            updated = conn.execute(
                """UPDATE app.review_cases SET status='PENDING', assignee_id=NULL, outcome=NULL,
                          skip_reason=NULL, close_note=NULL, closed_at=NULL, cycle_no=%s,
                          reopen_count=reopen_count+1, updated_at=%s, row_version=row_version+1
                   WHERE case_id=%s AND row_version=%s""",
                (cycle_no, now, case["case_id"], case["row_version"]),
            )
            if updated.rowcount != 1:
                raise WorkflowPolicyError(*_CONCURRENT)
            self._audit(
                conn, case, order_id, actor_id, "REOPEN", case["status"], "PENDING", clean_reason
            )

    def add_comment(
        self, order_id: str, actor_id: UUID, is_manager: bool, text: str
    ) -> dict[str, object]:
        """Append a comment; only the assignee or a Manager may write."""
        body = validate_comment(text)
        with self._connect() as conn, conn.transaction():
            case = self._lock_case(conn, order_id)
            if not is_manager and case["assignee_id"] != actor_id:
                raise WorkflowPolicyError("FORBIDDEN", "Only the assignee or a Manager may comment")
            row = conn.execute(
                """INSERT INTO app.case_comments(case_id, author_id, body) VALUES (%s,%s,%s)
                   RETURNING comment_id, created_at""",
                (case["case_id"], actor_id, body),
            ).fetchone()
            if row is None:
                raise RuntimeError("Comment insert returned no row")
            self._audit(conn, case, order_id, actor_id, "COMMENT", None, "comment", body)
            return {
                "comment_id": str(row["comment_id"]),
                "created_at": row["created_at"],
                "text": body,
            }

    def add_model_note(self, order_id: str, actor_id: UUID, note: str) -> dict[str, object]:
        """Record a Manager "review the model" note as an audit event; never touches ML output."""
        value = validate_comment(note)
        now = self._clock()
        with self._connect() as conn, conn.transaction():
            case = self._lock_case(conn, order_id)
            self._audit(conn, case, order_id, actor_id, "MODEL_NOTE", None, "note", value)
            return {"note": value, "created_at": now}

    def add_contact(self, command: AddContact) -> ContactResult:
        """Append an Attempt; the final unsuccessful one also closes the case atomically."""
        now = self._clock()
        ids = [e.file_id for e in command.evidence]
        validate_contact_inputs(
            command.method, command.contacted_at, command.next_contact_date, len(ids)
        )
        if len(set(ids)) != len(ids):
            raise WorkflowPolicyError("EVIDENCE_INVALID", "Evidence file ids must be unique")
        with self._connect() as conn, conn.transaction():
            case = self._lock_case(conn, command.order_id)
            if case["assignee_id"] != command.actor_id:
                raise WorkflowPolicyError("FORBIDDEN", "Only the current assignee may add contacts")
            cycle = self._open_cycle(conn, case["case_id"])
            if cycle is None:
                raise WorkflowPolicyError("INVALID_STATE", "The case has no open cycle")
            count = conn.execute(
                "SELECT count(*)::int AS n FROM app.contact_attempts WHERE cycle_id=%s",
                (cycle["cycle_id"],),
            ).fetchone()
            if count is None:
                raise RuntimeError("Attempt count query returned no row")
            snapshot = CaseSnapshot(
                case["status"],
                case["risk_level"],
                str(case["assignee_id"]),
                int(count["n"]),
                _param(conn, "max_contact", now),
                None,
                0,
            )
            auto_skip = validate_contact(snapshot, command.contacted_at, now, command.result)
            uploads = []
            for file_id in ids:
                upload = conn.execute(
                    """SELECT upload_id, storage_key, file_name, content_type, file_size
                       FROM app.evidence_uploads
                       WHERE upload_id=%s AND uploaded_by=%s AND attached_at IS NULL FOR UPDATE""",
                    (file_id, command.actor_id),
                ).fetchone()
                if upload is None:
                    raise WorkflowPolicyError(
                        "EVIDENCE_INVALID", "Evidence is unknown or already used"
                    )
                uploads.append(upload)
            assignment = conn.execute(
                "SELECT assignment_id FROM app.assignments WHERE case_id=%s AND released_at IS NULL",
                (case["case_id"],),
            ).fetchone()
            attempt_no = snapshot.contact_count + 1
            attempt = conn.execute(
                """INSERT INTO app.contact_attempts(case_id, assignment_id, attempt_no, channel,
                          status, attempted_at, outcome, created_by, created_at, cycle_id,
                          contact_result, note, next_contact_date, evidence_ref)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING attempt_id""",
                (
                    case["case_id"],
                    assignment["assignment_id"] if assignment else None,
                    attempt_no,
                    _CHANNEL[command.method],
                    "COMPLETED" if command.result == "REACHED" else "FAILED",
                    command.contacted_at,
                    command.result,
                    command.actor_id,
                    now,
                    cycle["cycle_id"],
                    command.result,
                    command.note,
                    command.next_contact_date,
                    command.evidence_ref,
                ),
            ).fetchone()
            if attempt is None:
                raise RuntimeError("Attempt insert returned no row")
            for upload in uploads:
                conn.execute(
                    """INSERT INTO app.contact_evidence(case_id, attempt_id, storage_key,
                              content_type, metadata, attached_at, expires_at, attached_by)
                       VALUES (%s,%s,%s,%s,%s,%s,'infinity',%s)""",
                    (
                        case["case_id"],
                        attempt["attempt_id"],
                        upload["storage_key"],
                        upload["content_type"],
                        Jsonb(
                            {
                                "upload_id": str(upload["upload_id"]),
                                "file_name": upload["file_name"],
                                "file_size": upload["file_size"],
                            }
                        ),
                        now,
                        command.actor_id,
                    ),
                )
                conn.execute(
                    "UPDATE app.evidence_uploads SET attached_at=%s WHERE upload_id=%s",
                    (now, upload["upload_id"]),
                )
            self._audit(
                conn,
                case,
                command.order_id,
                command.actor_id,
                "CONTACT",
                None,
                f"#{attempt_no} {command.method} · {command.result}",
                command.note,
            )
            if auto_skip:
                self._close(conn, case, "SKIPPED", None, "UNREACHABLE", None, now)
                self._audit(
                    conn,
                    case,
                    command.order_id,
                    command.actor_id,
                    "SKIP",
                    "IN_PROGRESS",
                    "SKIPPED · UNREACHABLE",
                    "Final contact attempt was unsuccessful",
                )
            else:
                self._bump(conn, case, now)
            return ContactResult(attempt_no, auto_skip)

    def add_decision(self, command: AddDecision) -> dict[str, object]:
        """Append a Manager Decision to the current cycle; it never changes status or scores."""
        now = self._clock()
        validate_decision(
            command.decision, command.reason, command.next_step, command.due_date, now.date()
        )
        with self._connect() as conn, conn.transaction():
            case = self._lock_case(conn, command.order_id)
            if command.next_step_assignee_id is not None:
                active = conn.execute(
                    "SELECT 1 FROM app.users WHERE user_id=%s AND is_active",
                    (command.next_step_assignee_id,),
                ).fetchone()
                if active is None:
                    raise WorkflowPolicyError(
                        "VALIDATION_ERROR", "next_step_assignee_id is not an active user"
                    )
            cycle = conn.execute(
                "SELECT cycle_id, cycle_no FROM app.review_cycles WHERE case_id=%s "
                "ORDER BY cycle_no DESC LIMIT 1",
                (case["case_id"],),
            ).fetchone()
            if cycle is None:
                raise RuntimeError("Case has no review cycle")
            reason = command.reason.strip()
            next_step = command.next_step.strip()
            row = conn.execute(
                """INSERT INTO app.manager_decisions(case_id, decided_by, decision, rationale,
                          created_at, cycle_id, next_step, next_step_assignee_id, due_date, note)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING decision_id""",
                (
                    case["case_id"],
                    command.actor_id,
                    command.decision,
                    reason,
                    now,
                    cycle["cycle_id"],
                    next_step,
                    command.next_step_assignee_id,
                    command.due_date,
                    command.note,
                ),
            ).fetchone()
            if row is None:
                raise RuntimeError("Decision insert returned no row")
            self._audit(
                conn,
                case,
                command.order_id,
                command.actor_id,
                "DECISION",
                None,
                command.decision,
                reason,
            )
            return {
                "decision_id": str(row["decision_id"]),
                "created_at": now,
                "cycle_no": int(cycle["cycle_no"]),
                "decision": command.decision,
                "reason": reason,
                "next_step": next_step,
                "next_step_assignee_id": command.next_step_assignee_id,
                "due_date": command.due_date,
                "note": command.note,
            }

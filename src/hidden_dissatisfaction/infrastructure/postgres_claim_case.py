"""Transactional PostgreSQL claim adapter."""

from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.application.claim import ClaimResult
from hidden_dissatisfaction.domain.workflow import CaseSnapshot, validate_claim


class ClaimConflictError(RuntimeError):
    """Another writer changed the claimable case."""


class ClaimNotFoundError(LookupError):
    """The requested order has no workflow case."""


class PostgresClaimCase:
    """Persist assignment, state transition, and audit event in one transaction."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def execute(self, order_id: str, actor_id: UUID) -> ClaimResult:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            with connection.transaction():
                connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (str(actor_id),))
                row = connection.execute(
                    """
                    SELECT c.case_id, c.status, c.assignee_id, c.row_version, r.risk_level,
                      (SELECT value::int FROM app.parameters WHERE param_key='capacity'
                       AND effective_at <= now() ORDER BY effective_at DESC, version DESC LIMIT 1) AS capacity
                    FROM app.review_cases c
                    JOIN ml.v_risk_orders_for_web r ON r.prediction_id=c.prediction_id AND r.order_id=c.order_id
                    WHERE c.order_id=%s FOR UPDATE OF c
                    """,
                    (order_id,),
                ).fetchone()
                if row is None:
                    raise ClaimNotFoundError(order_id)
                if row["capacity"] is None:
                    raise RuntimeError("No effective capacity parameter")
                capacity = int(row["capacity"])
                count_row = connection.execute(
                    "SELECT count(*)::int AS active_count FROM app.assignments WHERE assignee_id=%s AND released_at IS NULL",
                    (actor_id,),
                ).fetchone()
                if count_row is None:
                    raise RuntimeError("Claim workload query returned no row")
                active_count = int(count_row["active_count"])
                validate_claim(
                    CaseSnapshot(str(row["status"]), str(row["risk_level"]), None, 0, 0, None, 0),
                    str(actor_id),
                    active_count,
                    capacity,
                )
                updated = connection.execute(
                    """UPDATE app.review_cases SET status='IN_PROGRESS', assignee_id=%s,
                       updated_at=now(), row_version=row_version+1
                       WHERE case_id=%s AND row_version=%s AND status='PENDING' AND assignee_id IS NULL""",
                    (actor_id, row["case_id"], row["row_version"]),
                )
                if updated.rowcount != 1:
                    raise ClaimConflictError(order_id)
                connection.execute(
                    "INSERT INTO app.assignments(case_id, assignee_id) VALUES (%s, %s)",
                    (row["case_id"], actor_id),
                )
                connection.execute(
                    """INSERT INTO app.audit_events(case_id, order_id, actor_id, provenance, event_type, old_value, new_value)
                       VALUES (%s, %s, %s, 'USER', 'CLAIM', 'PENDING · (none)', 'IN_PROGRESS')""",
                    (row["case_id"], order_id, actor_id),
                )
                return ClaimResult(order_id, active_count + 1, capacity)

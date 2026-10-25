"""Re-derive SLA due times of OPEN cycles once a changed SLA parameter takes effect."""

from datetime import datetime, timedelta

import psycopg
from psycopg.rows import dict_row

_LEVEL_KEYS = ("sla_hours_high", "sla_hours_medium", "sla_hours_low")


class PostgresSlaRecalculator:
    """Idempotent: each (cycle, parameter version) is adjusted at most once."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def run(self, now: datetime) -> int:
        """Apply every SLA parameter version that became effective; return rows written."""
        written = 0
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute("SELECT pg_advisory_xact_lock(hashtext('app.sla_adjustments'))")
            for key in _LEVEL_KEYS:
                level = key.removeprefix("sla_hours_").upper()
                param = conn.execute(
                    """SELECT parameter_id, value::int AS hours, effective_at FROM app.parameters
                       WHERE param_key = %s AND effective_at <= %s
                       ORDER BY effective_at DESC, version DESC LIMIT 1""",
                    (key, now),
                ).fetchone()
                if param is None:
                    continue
                cycles = conn.execute(
                    """SELECT y.cycle_id, y.started_at FROM app.review_cycles y
                       JOIN app.review_cases c ON c.case_id = y.case_id
                       JOIN ml.v_risk_orders_for_web r
                         ON r.prediction_id = c.prediction_id AND r.order_id = c.order_id
                       WHERE y.ended_at IS NULL AND r.risk_level = %s
                         AND y.started_at < %s
                         AND NOT EXISTS (SELECT 1 FROM app.sla_adjustments a
                                         WHERE a.cycle_id = y.cycle_id AND a.parameter_id = %s)
                       FOR UPDATE OF y""",
                    (level, param["effective_at"], param["parameter_id"]),
                ).fetchall()
                for cycle in cycles:
                    due = cycle["started_at"] + timedelta(hours=int(param["hours"]))
                    conn.execute(
                        "INSERT INTO app.sla_adjustments(cycle_id, sla_due_at, parameter_id, applied_at) "
                        "VALUES (%s,%s,%s,%s)",
                        (cycle["cycle_id"], due, param["parameter_id"], now),
                    )
                    written += 1
        return written

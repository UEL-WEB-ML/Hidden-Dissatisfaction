"""Read models for P9 operational configuration and specialist assignment UI."""

from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row


class PostgresOperationalReadModel:
    """Serve read-only P9.1 projections without leaking database rows to routes."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def config(self, now: datetime) -> dict[str, object]:
        """Return the effective parameter bundle and active model thresholds."""
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            # Per key, the latest version already effective: bundles also contain
            # future-scheduled values, so they cannot answer "what applies now".
            parameter_rows = connection.execute(
                """
                SELECT DISTINCT ON (p.param_key) p.param_key, p.value,
                       (SELECT max(b.revision) FROM app.parameter_bundles b
                        JOIN app.parameters p2 ON p2.parameter_id = b.parameter_id
                        WHERE p2.effective_at <= %(now)s) AS revision
                FROM app.parameters p
                WHERE p.effective_at <= %(now)s
                ORDER BY p.param_key, p.effective_at DESC, p.version DESC
                """,
                {"now": now},
            ).fetchall()
            threshold = connection.execute(
                "SELECT threshold_version, medium_from, high_from FROM ml.v_active_thresholds"
            ).fetchone()
        if not parameter_rows:
            raise LookupError("no effective parameter bundle")
        if threshold is None:
            raise LookupError("no active model thresholds")
        values = {str(row["param_key"]): str(row["value"]) for row in parameter_rows}
        return {
            "parameter_version": f"bundle-{parameter_rows[0]['revision']}",
            "threshold_version": str(threshold["threshold_version"]),
            "medium_from": float(threshold["medium_from"]),
            "high_from": float(threshold["high_from"]),
            "sla_calendar": values["sla_calendar"],
            "sla_hours": {
                "HIGH": int(values["sla_hours_high"]),
                "MEDIUM": int(values["sla_hours_medium"]),
                "LOW": int(values["sla_hours_low"]),
            },
            "first_touch_hours": int(values["first_touch_hours"]),
            "capacity": int(values["capacity"]),
            "capacity_warn": int(values["capacity_warn"]),
            "max_contact": int(values["max_contact"]),
            "retry_gap_days": int(values["retry_gap_days"]),
            "soon_hours": int(values["soon_hours"]),
            "stale_hours": int(values["stale_hours"]),
            "aging_days": int(values["aging_days"]),
            "reopen_review_days": int(values["reopen_review_days"]),
            "reopen_review_times": int(values["reopen_review_times"]),
            "server_time": now,
        }

    def parameters(self, now: datetime) -> dict[str, object]:
        """Return immutable parameter history and the currently effective values."""
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            rows = connection.execute(
                """
                SELECT p.param_key AS key, p.value, p.version, p.effective_at, p.reason,
                       p.created_at, u.user_id AS actor_id, u.full_name AS actor_name,
                       d.unit, d.in_brd
                FROM app.parameters p
                JOIN app.parameter_definitions d ON d.param_key = p.param_key
                JOIN app.users u ON u.user_id = p.actor_id
                ORDER BY p.param_key, p.effective_at DESC, p.version DESC
                """
            ).fetchall()
        current: dict[str, dict[str, object]] = {}
        history: list[dict[str, object]] = []
        for row in rows:
            item = dict(row)
            item["status"] = "SCHEDULED" if item["effective_at"] > now else "SUPERSEDED"
            if item["key"] not in current and item["effective_at"] <= now:
                item["status"] = "ACTIVE"
                current[str(item["key"])] = item
            history.append(item)
        return {
            "parameter_version": "current",
            "server_time": now,
            "items": list(current.values()),
            "history": history,
        }

    def users(self, role: str | None, now: datetime) -> list[dict[str, Any]]:
        """Return active users with a workload snapshot calculated at query time."""
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            rows = connection.execute(
                """
                WITH capacity AS (
                    SELECT value::int AS value
                    FROM app.parameters
                    WHERE param_key = 'capacity' AND effective_at <= %(now)s
                    ORDER BY effective_at DESC, version DESC LIMIT 1
                )
                SELECT u.user_id, u.username, u.full_name, u.role, u.preferred_language,
                       u.created_at, count(a.assignment_id)::int AS active_count,
                       CASE WHEN u.role = 'SPECIALIST' THEN (SELECT value FROM capacity) END AS capacity
                FROM app.users u
                LEFT JOIN app.assignments a ON a.assignee_id = u.user_id AND a.released_at IS NULL
                WHERE u.is_active AND (%(role)s IS NULL OR u.role = %(role)s)
                GROUP BY u.user_id
                ORDER BY u.full_name, u.user_id
                """,
                {"role": role, "now": now},
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            capacity = item["capacity"]
            item["slots_left"] = (
                max(int(capacity) - int(item["active_count"]), 0) if capacity else None
            )
            result.append(item)
        return result

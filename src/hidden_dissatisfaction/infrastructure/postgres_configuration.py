"""Synchronous, read-only Postgres adapter for P9.1 configuration queries."""

from datetime import datetime
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.domain.configuration import (
    EffectiveParameterBundle,
    MLThresholds,
    WorkloadCapacity,
)


class PostgresConfigurationReader:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def effective_parameters(self, as_of: datetime) -> EffectiveParameterBundle:
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        sql = """
        SELECT b.revision, p.param_key, p.value
        FROM app.parameter_bundles b JOIN app.parameters p ON p.parameter_id=b.parameter_id
        WHERE p.effective_at <= %s
          AND b.revision = (SELECT max(b2.revision) FROM app.parameter_bundles b2
                            JOIN app.parameters p2 ON p2.parameter_id=b2.parameter_id
                            WHERE p2.effective_at <= %s)
        ORDER BY p.param_key
        """
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(sql, (as_of, as_of)).fetchall()
        if not rows:
            raise LookupError("no effective parameter bundle")
        return EffectiveParameterBundle(
            int(rows[0]["revision"]), as_of, {r["param_key"]: r["value"] for r in rows}
        )

    def user_workload_capacity(self, user_id: UUID) -> WorkloadCapacity:
        sql = """
        SELECT u.user_id, count(a.assignment_id)::int AS workload,
               coalesce((SELECT value::int FROM app.parameters WHERE param_key='capacity'
                         ORDER BY effective_at DESC, version DESC LIMIT 1), 0) AS capacity
        FROM app.users u LEFT JOIN app.assignments a ON a.assignee_id=u.user_id AND a.released_at IS NULL
        WHERE u.user_id=%s GROUP BY u.user_id
        """
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            row = conn.execute(sql, (user_id,)).fetchone()
        if row is None:
            raise LookupError("user not found")
        return WorkloadCapacity(str(row["user_id"]), int(row["workload"]), int(row["capacity"]))

    def ml_thresholds(self, model_release_id: UUID, threshold_version: str) -> MLThresholds:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            row = conn.execute(
                "SELECT model_release_id, threshold_version, medium_from, high_from FROM ml.model_thresholds WHERE model_release_id=%s AND threshold_version=%s",
                (model_release_id, threshold_version),
            ).fetchone()
        if row is None:
            raise LookupError("ML thresholds not found")
        return MLThresholds(
            str(row["model_release_id"]),
            row["threshold_version"],
            float(row["medium_from"]),
            float(row["high_from"]),
        )

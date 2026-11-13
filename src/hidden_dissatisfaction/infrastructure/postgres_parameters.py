"""PostgreSQL adapter for append-only operational parameter versions."""

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.application.parameters import (
    CreateParameterVersionCommand,
    ParameterVersion,
)
from hidden_dissatisfaction.domain.parameters import validate_parameter_change


class PostgresParameterVersionWriter:
    """Append parameter, revision snapshot, and audit event atomically."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def effective_values(self, as_of: datetime) -> Mapping[str, str]:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            return self._effective_values(connection, as_of)

    def append_version(
        self, command: CreateParameterVersionCommand, normalized_value: str, now: datetime
    ) -> ParameterVersion:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            with connection.transaction():
                connection.execute("SELECT pg_advisory_xact_lock(hashtext('app.parameters'))")
                effective_values = self._effective_values(connection, command.effective_at)
                normalized_value = validate_parameter_change(
                    key=command.key,
                    value=command.value,
                    effective_at=command.effective_at,
                    reason=command.reason,
                    now=now,
                    effective_values=effective_values,
                )
                version_row = connection.execute(
                    "SELECT coalesce(max(version), 0) + 1 AS version "
                    "FROM app.parameters WHERE param_key = %s",
                    (command.key,),
                ).fetchone()
                version = self._require_row(version_row)["version"]
                row = self._require_row(
                    connection.execute(
                        """
                    INSERT INTO app.parameters(param_key, version, value, effective_at, actor_id, reason)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING parameter_id, created_at
                    """,
                        (
                            command.key,
                            version,
                            normalized_value,
                            command.effective_at,
                            command.actor_id,
                            command.reason,
                        ),
                    ).fetchone()
                )
                revision_row = connection.execute(
                    "SELECT coalesce(max(revision), 0) + 1 AS revision FROM app.parameter_bundles"
                ).fetchone()
                revision = self._require_row(revision_row)["revision"]
                connection.execute(
                    """
                    INSERT INTO app.parameter_bundles(revision, parameter_id, created_by)
                    SELECT %s, parameter_id, %s
                    FROM (
                        SELECT DISTINCT ON (param_key) parameter_id
                        FROM app.parameters
                        WHERE effective_at <= %s
                        ORDER BY param_key, effective_at DESC, version DESC
                    ) AS effective_parameters
                    """,
                    (revision, command.actor_id, command.effective_at),
                )
                connection.execute(
                    """
                    INSERT INTO app.audit_events(
                        case_id, order_id, actor_id, actor_kind, provenance, event_type,
                        old_value, new_value, reason
                    )
                    VALUES (NULL, NULL, %s, 'USER', 'USER', 'PARAMETER_CHANGE', %s, %s, %s)
                    """,
                    (
                        command.actor_id,
                        effective_values.get(command.key),
                        json.dumps({"key": command.key, "value": normalized_value}),
                        command.reason,
                    ),
                )
        return ParameterVersion(
            key=command.key,
            value=normalized_value,
            version=version,
            effective_at=command.effective_at,
            actor_id=command.actor_id,
            reason=command.reason,
            created_at=row["created_at"],
        )

    @staticmethod
    def _effective_values(
        connection: psycopg.Connection[dict[str, object]], as_of: datetime
    ) -> dict[str, str]:
        rows = connection.execute(
            """
            SELECT DISTINCT ON (param_key) param_key, value
            FROM app.parameters
            WHERE effective_at <= %s
            ORDER BY param_key, effective_at DESC, version DESC
            """,
            (as_of,),
        ).fetchall()
        return {str(row["param_key"]): str(row["value"]) for row in rows}

    @staticmethod
    def _require_row(row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            raise RuntimeError("PostgreSQL statement unexpectedly returned no row")
        return row

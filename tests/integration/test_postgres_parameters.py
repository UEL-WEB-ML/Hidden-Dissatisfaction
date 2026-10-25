"""DSN-gated integration coverage for the P9.1 parameter write transaction."""

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
import pytest

from hidden_dissatisfaction.application.parameters import CreateParameterVersionCommand
from hidden_dissatisfaction.infrastructure.postgres_configuration import PostgresConfigurationReader
from hidden_dissatisfaction.infrastructure.postgres_parameters import PostgresParameterVersionWriter

SETUP_DSN = os.environ.get("P9_TEST_POSTGRES_DSN")
RUNTIME_DSN = os.environ.get("P9_APP_RUNTIME_DSN")
pytestmark = pytest.mark.integration


def test_parameter_append_is_audited_and_future_revision_is_not_effective_early() -> None:
    if not SETUP_DSN or not RUNTIME_DSN:
        pytest.skip("P9_TEST_POSTGRES_DSN and P9_APP_RUNTIME_DSN are required")
    setup_dsn = SETUP_DSN
    runtime_dsn = RUNTIME_DSN
    manager_id = uuid4()
    now = datetime.now(UTC).replace(microsecond=0)
    future = now + timedelta(hours=1)
    with psycopg.connect(setup_dsn) as setup:
        setup.execute(
            """
            INSERT INTO app.users(user_id, username, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, 'MANAGER')
            """,
            (manager_id, f"parameter-{str(manager_id)[:8]}", "not-used", "Parameter Manager"),
        )

    result = PostgresParameterVersionWriter(runtime_dsn).append_version(
        CreateParameterVersionCommand(
            key="capacity",
            value=6,
            effective_at=future,
            reason="Integration test shift",
            actor_id=manager_id,
        ),
        normalized_value="6",
        now=now,
    )

    assert result.version >= 2
    assert result.value == "6"
    with psycopg.connect(setup_dsn) as verify:
        assert verify.execute(
            """
            SELECT 1 FROM app.audit_events
            WHERE actor_id=%s AND event_type='PARAMETER_CHANGE' AND order_id IS NULL
            """,
            (manager_id,),
        ).fetchone()
        revision_count = verify.execute(
            "SELECT count(*) FROM app.parameter_bundles WHERE revision >= 2"
        ).fetchone()
        assert revision_count is not None
        assert revision_count[0] >= 14

    current = PostgresConfigurationReader(runtime_dsn).effective_parameters(now)
    assert current.value("capacity") == "5"
    future_bundle = PostgresConfigurationReader(runtime_dsn).effective_parameters(future)
    assert future_bundle.value("capacity") == "6"

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

    before = PostgresConfigurationReader(runtime_dsn).effective_parameters(now).value("capacity")
    scheduled_capacity = str(int(before) + 7)
    result = PostgresParameterVersionWriter(runtime_dsn).append_version(
        CreateParameterVersionCommand(
            key="capacity",
            value=int(scheduled_capacity),
            effective_at=future,
            reason="Integration test shift",
            actor_id=manager_id,
        ),
        normalized_value=scheduled_capacity,
        now=now,
    )

    assert result.version >= 2
    assert result.value == scheduled_capacity
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
    assert current.value("capacity") == before
    future_bundle = PostgresConfigurationReader(runtime_dsn).effective_parameters(future)
    assert future_bundle.value("capacity") == scheduled_capacity


def _manager(setup_dsn: str) -> object:
    manager_id = uuid4()
    with psycopg.connect(setup_dsn) as setup:
        setup.execute(
            "INSERT INTO app.users(user_id, username, password_hash, full_name, role) "
            "VALUES (%s, %s, 'x', 'Race Manager', 'MANAGER')",
            (manager_id, f"race-{manager_id.hex[:8]}"),
        )
    return manager_id


def test_config_reports_the_value_effective_now_not_a_scheduled_one() -> None:
    from hidden_dissatisfaction.infrastructure.postgres_operational_reads import (
        PostgresOperationalReadModel,
    )

    if not SETUP_DSN or not RUNTIME_DSN:
        pytest.skip("P9_TEST_POSTGRES_DSN and P9_APP_RUNTIME_DSN are required")
    manager_id = _manager(SETUP_DSN)
    now = datetime.now(UTC).replace(microsecond=0)
    writer = PostgresParameterVersionWriter(RUNTIME_DSN)
    reads = PostgresOperationalReadModel(RUNTIME_DSN)
    before = reads.config(now)["soon_hours"]
    scheduled = int(before) % 700 + 3  # type: ignore[call-overload]
    writer.append_version(
        CreateParameterVersionCommand("soon_hours", scheduled, now + timedelta(days=2), "later", manager_id),  # type: ignore[arg-type]
        str(scheduled),
        now,
    )
    assert reads.config(now)["soon_hours"] == before
    assert reads.config(now + timedelta(days=3))["soon_hours"] == scheduled


def test_concurrent_parameter_writes_serialize_without_duplicate_versions() -> None:
    from concurrent.futures import ThreadPoolExecutor

    if not SETUP_DSN or not RUNTIME_DSN:
        pytest.skip("P9_TEST_POSTGRES_DSN and P9_APP_RUNTIME_DSN are required")
    manager_id = _manager(SETUP_DSN)
    runtime_dsn = RUNTIME_DSN
    now = datetime.now(UTC).replace(microsecond=0)
    when = now + timedelta(days=30)

    def write(value: int) -> int:
        return (
            PostgresParameterVersionWriter(runtime_dsn)
            .append_version(
                CreateParameterVersionCommand("stale_hours", value, when, "race", manager_id),  # type: ignore[arg-type]
                str(value),
                now,
            )
            .version
        )

    with ThreadPoolExecutor(6) as pool:
        versions = sorted(pool.map(write, range(40, 46)))
    assert versions == list(range(versions[0], versions[0] + 6))
    with psycopg.connect(SETUP_DSN) as check:
        audit = check.execute(
            "SELECT count(*) FROM app.audit_events WHERE actor_id=%s AND event_type='PARAMETER_CHANGE'",
            (manager_id,),
        ).fetchone()
        revisions = check.execute(
            "SELECT count(DISTINCT revision) FROM app.parameter_bundles WHERE created_by=%s",
            (manager_id,),
        ).fetchone()
    assert audit is not None and audit[0] == 6
    assert revisions is not None and revisions[0] == 6

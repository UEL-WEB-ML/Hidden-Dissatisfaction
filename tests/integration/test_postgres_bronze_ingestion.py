import csv
import os
from pathlib import Path

import psycopg
import pytest

from hidden_dissatisfaction.application.bronze_ingestion import BRONZE_FILE_SPECS, build_manifest
from hidden_dissatisfaction.infrastructure.postgres_bronze_ingestion import PostgresBronzeLoader


@pytest.fixture
def bronze_dsn() -> str:
    """Require an explicitly configured migrated PostgreSQL verification database."""

    dsn = os.environ.get("BRONZE_TEST_DSN")
    if not dsn:
        pytest.skip("BRONZE_TEST_DSN is required for PostgreSQL Bronze integration tests")
    return dsn


def write_fixture(raw_dir: Path) -> None:
    """Write one valid row to every allowlisted raw relation."""

    for spec in BRONZE_FILE_SPECS:
        with (raw_dir / spec.filename).open("w", encoding="utf-8", newline="") as target:
            writer = csv.writer(target)
            writer.writerow(spec.headers)
            writer.writerow([f"{spec.table_name}_{index}" for index in range(len(spec.headers))])


@pytest.mark.integration
def test_postgres_loader_creates_two_complete_historical_runs(
    tmp_path: Path, bronze_dsn: str
) -> None:
    """Load a tiny snapshot twice without overwriting either historical run."""

    write_fixture(tmp_path)
    manifest = build_manifest(tmp_path)
    loader = PostgresBronzeLoader(bronze_dsn)

    first_run = loader.load(tmp_path, manifest)
    second_run = loader.load(tmp_path, manifest)

    assert first_run != second_run
    with psycopg.connect(bronze_dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM bronze.ingestion_runs WHERE run_id IN (%s, %s) ORDER BY run_id",
                (first_run, second_run),
            )
            assert [row[0] for row in cursor.fetchall()] == ["COMPLETE", "COMPLETE"]
            cursor.execute(
                "SELECT count(*) FROM bronze.orders WHERE run_id IN (%s, %s)",
                (first_run, second_run),
            )
            assert cursor.fetchone() == (2,)

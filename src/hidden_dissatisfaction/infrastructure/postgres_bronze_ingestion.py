"""PostgreSQL adapter for an immutable, run-scoped Bronze load."""

import json
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from hidden_dissatisfaction.application.bronze_ingestion import (
    BRONZE_FILE_SPECS,
    iter_csv_rows,
    validate_manifest,
)


class PostgresBronzeLoader:
    """Load one validated raw snapshot with a transaction-scoped advisory lock."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def load(
        self, raw_dir: Path, manifest: Mapping[str, Any], run_id: uuid.UUID | None = None
    ) -> uuid.UUID:
        """Persist a new complete run, or record a failed run after a load error."""

        import psycopg

        validate_manifest(raw_dir, manifest)
        identifier = run_id or uuid.uuid4()
        with psycopg.connect(self._dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtext('hidden-dissatisfaction-bronze'))"
                )
                cursor.execute(
                    "INSERT INTO bronze.ingestion_runs (run_id, status, manifest) VALUES (%s, 'STARTED', %s::jsonb)",
                    (identifier, json.dumps(manifest, sort_keys=True)),
                )
            connection.commit()
            try:
                with connection.cursor() as cursor:
                    for spec in BRONZE_FILE_SPECS:
                        columns = ", ".join(("run_id", *spec.headers))
                        with cursor.copy(
                            f"COPY bronze.{spec.table_name} ({columns}) FROM STDIN"
                        ) as copy:
                            for row in iter_csv_rows(raw_dir / spec.filename, spec.headers):
                                copy.write_row((identifier, *row))
                    cursor.execute(
                        "UPDATE bronze.ingestion_runs SET status = 'COMPLETE', completed_at = now() WHERE run_id = %s",
                        (identifier,),
                    )
                connection.commit()
            except Exception as error:
                connection.rollback()
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE bronze.ingestion_runs SET status = 'FAILED', failed_at = now(), failure_reason = %s WHERE run_id = %s",
                        (str(error)[:2000], identifier),
                    )
                connection.commit()
                raise
        return identifier

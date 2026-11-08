"""Retention job for unattached evidence uploads (ADR-006)."""

from datetime import datetime, timedelta
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def purge_unattached_uploads(dsn: str, root: Path, now: datetime, retention_hours: int = 24) -> int:
    """Delete uploads never attached to an Attempt; attached evidence is never touched.

    Files go first, then rows: a crash between the two leaves a row without a file,
    which the next run removes, instead of a file nothing references.
    """
    cutoff = now - timedelta(hours=retention_hours)
    removed = 0
    with psycopg.connect(dsn, row_factory=dict_row, autocommit=True) as conn:
        rows = conn.execute(
            "SELECT upload_id, storage_key FROM app.evidence_uploads "
            "WHERE attached_at IS NULL AND uploaded_at < %s",
            (cutoff,),
        ).fetchall()
        for row in rows:
            path = (root / row["storage_key"]).resolve()
            if root.resolve() in path.parents:
                path.unlink(missing_ok=True)
            deleted = conn.execute(
                "DELETE FROM app.evidence_uploads WHERE upload_id = %s AND attached_at IS NULL",
                (row["upload_id"],),
            )
            removed += deleted.rowcount
    return removed

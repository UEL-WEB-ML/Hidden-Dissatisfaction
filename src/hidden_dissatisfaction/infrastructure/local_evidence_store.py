"""Local-volume evidence storage (ADR-006 dev adapter); swap for object storage via the same API."""

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.domain.workflow import detect_evidence_type

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_file_name(name: str | None) -> str:
    """Keep the base name only, ASCII-safe and at most 100 characters."""
    base = _SAFE.sub("_", Path((name or "").replace("\\", "/")).name).strip("._")
    return (base or "file")[-100:]


class EvidenceNotFoundError(LookupError):
    """No stored evidence with this id."""


class EvidenceAccessError(PermissionError):
    """The caller may not read this evidence."""


class LocalEvidenceStore:
    """Writes validated files under ``root`` and records them as unattached uploads."""

    def __init__(self, dsn: str, root: Path) -> None:
        self._dsn = dsn
        self._root = root

    def save(self, owner_id: UUID, file_name: str | None, data: bytes) -> dict[str, Any]:
        """Validate by signature and size, store atomically, then record the upload."""
        content_type, extension = detect_evidence_type(data[:16], len(data))
        now = datetime.now(UTC)
        key = f"evidence/{now:%Y/%m}/{uuid4().hex}.{extension}"  # server-generated: no traversal
        target = self._root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".part")
        partial.write_bytes(data)
        os.replace(partial, target)
        clean = sanitize_file_name(file_name)
        try:
            with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
                row = conn.execute(
                    """INSERT INTO app.evidence_uploads(uploaded_by, storage_key, file_name,
                              content_type, file_size) VALUES (%s,%s,%s,%s,%s) RETURNING upload_id""",
                    (owner_id, key, clean, content_type, len(data)),
                ).fetchone()
        except psycopg.Error:
            target.unlink(missing_ok=True)
            raise
        if row is None:
            raise RuntimeError("Upload insert returned no row")
        file_id = str(row["upload_id"])
        return {
            "file_id": file_id,
            "file_name": clean,
            "file_type": content_type,
            "file_size": len(data),
            "url": f"/api/v1/files/{file_id}",
        }

    def locate(self, upload_id: UUID, user_id: UUID, is_manager: bool) -> tuple[Path, str, str]:
        """Return ``(path, content_type, file_name)`` for the uploader, a Manager or the assignee."""
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            row = conn.execute(
                """SELECT u.storage_key, u.content_type, u.file_name, u.uploaded_by,
                          EXISTS (SELECT 1 FROM app.contact_evidence e
                                  JOIN app.review_cases c ON c.case_id = e.case_id
                                  WHERE e.metadata ->> 'upload_id' = u.upload_id::text
                                    AND c.assignee_id = %(user)s) AS is_case_assignee
                   FROM app.evidence_uploads u WHERE u.upload_id = %(id)s""",
                {"id": upload_id, "user": user_id},
            ).fetchone()
        if row is None:
            raise EvidenceNotFoundError(str(upload_id))
        if not (is_manager or row["uploaded_by"] == user_id or row["is_case_assignee"]):
            raise EvidenceAccessError(str(upload_id))
        path = (self._root / row["storage_key"]).resolve()
        if self._root.resolve() not in path.parents or not path.is_file():
            raise EvidenceNotFoundError(str(upload_id))
        return path, row["content_type"], row["file_name"]

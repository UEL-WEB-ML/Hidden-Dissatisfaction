# ADR-006: Evidence storage and retention

## Context

Contact evidence is sensitive and must remain authorized, append-only once
attached, and replaceable with object storage without changing workflow rules.

## Decision

Use an `EvidenceStorage` port. Development and tests use the local evidence
volume; a future object-storage adapter implements the same port. Only PNG,
JPG/JPEG, and PDF are accepted, with at most three files per attempt and a 5 MB
limit per file. Unattached uploads expire after 24 hours; attached evidence is
retained under the approved policy and is never publicly served.

## Alternatives

- Store file bytes directly in PostgreSQL.
- Allow arbitrary external links.
- Keep unattached uploads indefinitely.

## Consequences

The API validates signature, MIME type, size, ownership, and attachment state.
Cleanup removes only expired unattached uploads; download authorization is
enforced again for attached evidence.

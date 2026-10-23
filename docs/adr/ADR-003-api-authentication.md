# ADR-003: API authentication foundation

## Decision

P8 uses Bearer JWT access tokens with UTC ISO-8601 timestamps. Passwords are
hashed with Argon2 via `pwdlib`. Logout is stateless in the MVP and returns
`204 No Content`; no token revocation persistence is introduced. Database
migrations are explicit operational commands and never run at application
startup. Production migrations do not seed users.

## Consequences

JWT validation is self-contained and horizontally scalable, while logout does
not invalidate an already issued token. A future revocation strategy requires
a new ADR. API validation uses strict Pydantic schemas and a localized-ready
error envelope (`error.code` and `error.message`).

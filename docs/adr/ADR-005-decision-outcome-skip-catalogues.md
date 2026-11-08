# ADR-005: Decision, outcome and skip catalogues

## Status

Accepted as the API 0.5 catalogue. **Awaiting Product Owner confirmation**; a
change requires a new API Contract version, not a code-only edit.

## Decision

- `outcome`: `HAS_ISSUE`, `NO_ISSUE`, `DUPLICATE`. `UNREACHABLE` is not an outcome.
- `skip_reason`: `UNREACHABLE`, `DUPLICATE`, `REFUSED`, `NOT_APPLICABLE`, `OTHER`
  (`OTHER` requires a note). `UNREACHABLE` is set only by the final unsuccessful
  Attempt.
- `decision`: `NO_FURTHER_ACTION`, `FOLLOW_UP_CUSTOMER`, `WORK_WITH_SELLER`,
  `REFER_AFTER_SALES`.

The catalogues are enforced in three places that must change together: the domain
constants in `domain/workflow.py`, the database CHECK constraints, and API
Contract 2.6.

## Consequences

Adding a value is a versioned contract change plus a forward-only migration.

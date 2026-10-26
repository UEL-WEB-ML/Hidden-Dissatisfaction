# ADR-002: Timezone and API datetimes

## Context

Delivery, SLA, audit, and prediction timestamps cross database, API, and UI
boundaries. Ambiguous timestamps make temporal cutoffs non-reproducible.

## Decision

Store operational timestamps as PostgreSQL `timestamptz` in UTC. API responses
use ISO-8601 timestamps with an explicit offset. The frontend localizes only
for presentation. Dataset manifests retain the raw-source timezone assumption
and normalized cutoff policy.

## Alternatives

- Store local timestamps without an offset.
- Convert timestamps in browser code before persistence.

## Consequences

Server clocks and SLA comparisons use UTC. Database/API serializers must reject
ambiguous write values rather than silently applying a browser timezone.

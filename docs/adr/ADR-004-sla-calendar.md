# ADR-004: SLA calendar

## Status

Accepted for the MVP. The `BUSINESS_HOURS` activation is deferred.

## Context

`sla_calendar` accepts `CALENDAR` or `BUSINESS_HOURS` (API Contract 2.6). No work
schedule or holiday table exists, so business-hour arithmetic would be a guess.

## Decision

The MVP computes every SLA with `CALENDAR` (wall-clock hours). The parameter
stays configurable, but `sla_due_at` is always `cycle.started_at + hours`.
`BUSINESS_HOURS` is switched on only when a work-schedule and holiday table
exists and this ADR is superseded.

Changing an `sla_hours_*` parameter re-derives due times of OPEN cycles through
`hidden-dissatisfaction recalculate-sla`. The derived value is appended to
`app.sla_adjustments`; `review_cycles.sla_due_at`, closed cycles and audit
history are never rewritten. Reads use the latest adjustment when present.

## Alternatives

- Compute `BUSINESS_HOURS` now with a hard-coded Mon-Fri schedule: rejected,
  invents a rule the business has not approved.
- Rewrite `sla_due_at` in place: rejected, the V008 guard keeps cycles immutable.

## Consequences

- SLA values are comparable and reproducible from stored inputs.
- Selecting `BUSINESS_HOURS` today changes nothing; documented, not silent.

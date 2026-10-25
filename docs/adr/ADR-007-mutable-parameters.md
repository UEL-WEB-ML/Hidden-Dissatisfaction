# ADR-007: Mutable parameters

## Status

Accepted for the MVP: every key in `app.parameter_definitions` is Manager-editable.

## Context

`aging_days`, `soon_hours` and `stale_hours` have `in_brd = false`: the BRD does
not list them, but Queue/Dashboard flags depend on them.

## Decision

All fourteen keys may be changed by a Manager through `POST /parameters`, subject
to the range and cross-rule validation in `domain/parameters.py`, a mandatory
reason, and a future-or-current `effective_at`. ML thresholds are **not**
parameters; they come from the active model release and are read-only in
`/config`. The `SELLER_HOTSPOT` dashboard action keeps fixed thresholds (at least
3 HIGH orders and at least 50 percent of the seller's orders) until the Product
Owner decides whether they become parameters.

## Consequences

Making a key read-only later is a migration of `parameter_definitions` plus a
validation change, with no effect on stored history.

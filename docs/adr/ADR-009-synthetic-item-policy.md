# ADR-009: Synthetic item policy

## Context

The demo needs deterministic records, but synthetic records must not be
mistaken for Olist observations or empirical model evidence.

## Decision

Do not create synthetic items in a production Olist scoring run when raw item
records are available. Synthetic records are permitted only in explicit demo or
test fixtures and must carry `synthetic_data_flag = true` plus provenance.

## Alternatives

- Backfill missing raw items with synthetic records.
- Mix synthetic and real records without a marker.

## Consequences

Web views expose the synthetic marker. Synthetic/demo metrics and screenshots
cannot support performance, customer-impact, or causal claims.

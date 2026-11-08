# ADR-013: P5 v4 delivery and product features

## Status

Accepted.

## Decision

The v4 feature schema adds delivery buffer, purchase/carrier-to-delivery durations,
order composition/value-share, and product physical metadata. Every field is known
at or before `prediction_at`; review data remains excluded. Model selection retains
the v3 candidates and temporal protocol, but uses the new schema version
`p5-item-v2-delivery-product`. The sealed test remains untouched.

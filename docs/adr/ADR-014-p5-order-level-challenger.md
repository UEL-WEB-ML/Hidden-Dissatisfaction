# ADR-014: P5 v5 order-level challenger

## Status

Accepted.

## Decision

Add `order_aggregate` as a challenger regime because the observed review label and
primary metric are order-grained. Items are aggregated deterministically per order:
prices and freight are summed, item share uses the maximum concentration, physical
and historical measures use the mean, binary support flags use the maximum, and
categories use a sorted set. Temporal partitions remain frozen and aggregation is
performed independently inside every fit/evaluation partition. Calibration and
threshold selection must use the same grain as the selected regime. The sealed
final test remains untouched.

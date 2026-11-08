# ADR-001: Multiple-review policy

## Context

An Olist order can have multiple review records, while the modelling and
workflow grains require one observed label per order.

## Decision

Use the latest answered review. Order by answered timestamp descending, then
review-creation timestamp descending, then review identifier ascending as a
deterministic tie-break. Preserve review-count and multiple-review flags only
as lineage/uncertainty metadata. `negative = 1` for a selected score of 1 or 2.

## Alternatives

- Use the first review.
- Average or take the minimum review score.
- Exclude orders with multiple reviews.

## Consequences

`order_reviews_canonical` is the single resolution point. A sensitivity policy
may be compared only when versioned; it must not overwrite the canonical label
or be presented as causal attribution.

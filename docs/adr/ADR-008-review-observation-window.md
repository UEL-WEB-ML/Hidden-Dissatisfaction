# ADR-008: Review observation window

## Decision

P4 predicts at `delivered_customer_date`. The primary cohort requires non-null
delivery and estimated dates, delivery no later than the estimate, a canonical
review selected by ADR-001, and `review_creation_date > prediction_at`.
Equality is excluded. Review content, review timestamps, and review identifiers
are labels/lineage only and are never model features. Historical seller and
product/category aggregates include only events satisfying both strict cutoffs:
`prior.prediction_at < current.prediction_at` and
`prior.review_created_at < current.prediction_at`. Aggregates with fewer than
five observations are null and expose a low-support flag.

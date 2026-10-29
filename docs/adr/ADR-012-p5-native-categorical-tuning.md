# ADR-012: P5 v3 native-categorical CatBoost tuning

## Status

Accepted. This decision supersedes the GPU candidate set in ADR-011 while retaining
every prior CPU and GPU candidate as a comparison baseline.

## Context

The v2 winner (`catboost-gpu-depth8-v1`) was trained on ordinal-encoded categorical
fields. Olist's `product_category` and `customer_state` are complete string fields;
native CatBoost categorical handling can learn category statistics without imposing an
arbitrary numeric ordering. This is a targeted representation change, not an
unbounded hyperparameter search.

## Decision

- The protocol identifier is `p5-v3-native-catboost-tuning`.
- Add exactly one candidate: `catboost-gpu-native-depth8-v2` with native
  `product_category` and `customer_state`, 750 iterations, depth 8, learning rate
  0.04, L2 leaf regularization 5, balanced classes, seed 42, and GPU device `0`.
- Retain all v2 candidates, temporal partitions, three score regimes, selection
  rule, calibration split, and threshold policy unchanged.
- The tuning stop gate is a holdout order-level PR-AUC of at least 0.25 and an
  absolute improvement of at least 0.03 over the strongest non-tuned baseline. If
  it is met, stop candidate expansion; otherwise report the result and do not tune
  against the sealed test set.
- Final-test finalization remains forbidden until a new selection record is frozen.

## Consequences

The candidate can exploit categorical structure without treating category codes as
ordered values. The stop gate prevents indefinite search and preserves an auditable
development-only protocol.

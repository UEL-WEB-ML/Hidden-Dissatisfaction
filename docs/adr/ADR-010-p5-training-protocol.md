# ADR-010: P5 v1 training protocol

## Status

Accepted. This ADR freezes the P5 v1 training and evaluation scope.

## Context

P5 follows the accepted latest answer to ADR-001. The protocol must preserve the
order-level label and temporal leakage controls while making model selection,
calibration, prioritization, and final evaluation reproducible.

## Decision

- P4 release-gate evidence is a prerequisite for P5 execution.
- The primary selection order is maximum v1 order-level PR-AUC. Item-level PR-AUC
  remains a reported diagnostic.
- The fixed candidate set is prevalence baseline, Logistic Regression, Random
  Forest, and histogram gradient boosting. CatBoost is excluded from P5 v1.
- Item scoring is compared under three policies: unweighted item score,
  `order_weight`, and the order reference policy. Order aggregation uses the
  versioned `max-v1` rule.
- Development uses five temporal segments, with all items from an order kept
  together, followed by a sealed final-test segment.
- Calibration fitting and calibration comparison are separate operations on
  independent development data. Calibration cannot use the sealed test.
- Item calibration wording and order-priority score ordering are recorded as part
  of the locked output specification.
- Threshold policy is fixed before final evaluation: high priority is the top 5%
  and medium priority extends through the top 20%.
- Uncertainty uses 1,000 order-cluster bootstrap resamples, not item-level
  resampling.
- After model, calibration, score policy, wording, and thresholds are locked,
  the final test is run once. No subsequent test-driven selection is permitted.

## Consequences

P5 results are comparable across candidates and protected from item-level and
test-period leakage. The protocol limits model breadth and does not permit
post-lock tuning based on final-test results. Any change requires a new ADR or
an explicit superseding decision.

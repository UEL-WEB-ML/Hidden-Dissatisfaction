# P5 development gate — 2026-10-23

This record contains aggregate, non-row-level evidence only. It is not a final-test report.

## P4 prerequisite

- Bronze run: `5bc156d8-bd29-49d9-b4cf-136d7102a6f6` (`complete`).
- dbt build: 68 passed, 0 warnings, 0 errors, 0 skipped.
- release-only history test: 1 passed, 0 warnings, 0 errors.
- exported dataset: 97,884 product items across 85,425 orders.
- stable item-key validation: passed (`order_id || '-' || order_item_id`).
- dataset SHA-256: `6f9abe68437dedcf0d81c57b11737007ba83576a84b0bbca2dc1c47a9a8369ba`.
- manifest SHA-256: `c5c4b29624a6a8089d0cc6095d664bcda261d96decd8ca549bf027032f2749fa`.

## Development selection

- Selected variant: `hist_gradient_boosting-l2-5-leaf15-v1`.
- Weighting regime: `item_unweighted`.
- Calibration: `isotonic`.
- Threshold policy: order-ranked top 5% HIGH and top 20% MEDIUM-or-higher.
- `high_from`: `0.2875`.
- `medium_from`: `0.1665024630541872`.

## Sealed-test controls

- Run status: `development`.
- No test metrics, predictions, budget metrics, or artifact inventory were emitted.
- Test metadata exposes only item/order counts and timestamp range.
- Test prevalence and target-class diagnostics are redacted until a valid finalization lock passes.
- Existing historical final-test results remain exploratory under `docs/incident-disclosure-p5.md`.
- No confirmatory finalization is authorized without a genuinely untouched replacement holdout.

## Code quality

- Ruff: passed.
- Black: passed.
- mypy: passed across 29 source/test files.
- pytest: 28 passed.

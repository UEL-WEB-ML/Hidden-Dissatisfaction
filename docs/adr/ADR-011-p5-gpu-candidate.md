# ADR-011: P5 v2 GPU candidate selection

## Status

Accepted. This decision supersedes only the P5 candidate-set restriction in ADR-010.

## Context

The local execution environment has a verified NVIDIA GPU. The original P5 v1
selection record was development-only, so the sealed test partition has not been
used to choose an estimator. A GPU-capable candidate can therefore be added without
post-test tuning, provided the comparison remains bounded and reproducible.

## Decision

- The protocol identifier is `p5-v2-gpu-selection`.
- Retain all seven v1 CPU variants as baselines and add exactly one candidate:
  `catboost-gpu-depth8-v1` (500 iterations, depth 8, learning rate 0.05, balanced
  classes, seed 42, GPU device `0`).
- Apply the existing order-grouped temporal folds, three score regimes, selection
  rule, calibration split, and development-only threshold policy unchanged.
- Record the GPU candidate parameters, protocol version, package version, and
  device selection in the development report and selection record.
- Do not run or inspect the sealed final-test partition during this comparison. A
  new frozen selection record and matching lock remain required for finalization.

## Consequences

The model choice is based on an auditable CPU-versus-GPU development comparison,
not GPU availability alone. Any further candidate expansion, hyperparameter search,
or test evaluation requires another explicit protocol decision.

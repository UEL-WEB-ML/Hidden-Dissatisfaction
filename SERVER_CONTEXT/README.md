# Server context for Chapters 3–4

Prepared from versioned, aggregate-only development artefacts already in this repository. No Olist raw data, row-level test predictions, model binaries, or secrets are included here.

## Contents

- `chapter3_evidence.md`: requested items 1–6.
- `chapter4_evidence.md`: requested items 7–11 and clear availability status.
- `rolling_origin_folds.md`: actual fold dates for Figure 3.3.
- `model_variant_fold_metrics.md`: complete metrics currently retained by variant, plus explicit gaps.
- `label_snapshot_build_evidence.md`: available dbt snapshot-build-log evidence and the unreconciled funnel gap.

## Source artefacts

- `reports/experiments/p5-s6-e15-content.json`: retained Random Forest run and rolling folds.
- `reports/experiments/p5-s10-gpu-tuning.json`: bounded GPU challenger run.
- `artifacts/checkpoints/p5-s10-gpu-tuning-selection.json`: GPU selection record.
- `configs/experiment.toml`: protocol boundaries and candidate grid.
- `docs/evidence/P5-development-gate-2026-10-23.md`: finalization gate.

All results are development/exploratory only. The historical test interval was not finalized; a genuinely untouched replacement holdout is required for confirmatory claims.

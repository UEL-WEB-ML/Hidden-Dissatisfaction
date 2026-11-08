# P12 Gate 0 — documentation and release boundary

Status: **Gate 0 documented; confirmatory release blocked**
Scope: Hidden-Dissatisfaction repository and its currently checked-in evidence.

Gate 0 defines what may be shown or claimed at this point. It does not promote
the model, create a new evaluation, or change code, data, or metrics.

## Evidence matrix

| Major artifact | Status | Permitted use and basis |
|---|---|---|
| Project, product, API, data and architecture contracts | **ready** | Authoritative definition of scope, grain, prediction time, weak-label interpretation, and interfaces. These documents are release documentation, not empirical evidence. |
| Research design and modeling/training plan | **ready** | Authoritative protocol and implementation checklist. Checked boxes describe implementation; they do not establish final-test completion. |
| P4 release-gate record referenced by the P5 evidence | **ready** | May substantiate the stated prerequisite and dataset lineage only as recorded in [`P5-development-gate-2026-10-23.md`](P5-development-gate-2026-10-23.md). |
| P5 development-gate evidence | **exploratory-only** | May describe the selected development configuration and development controls. It contains no final-test metrics or confirmatory artifact inventory. |
| Existing training runs, historical final-test outputs, and recovery rerun | **exploratory-only** | May be retained for engineering history and incident disclosure only. They must keep `evaluation_status: exploratory_non_confirmatory`. |
| Notebooks, reports, figures, predictions, and generated model artifacts | **exploratory-only** | May be used for development or a clearly labelled demo when present. They are not automatically evidence of a sealed evaluation. |
| Product-item final results and confirmatory performance claims | **blocked** | The implementation checklist still has outstanding product-item and final-evaluation work, and no valid replacement holdout has been authorized. |
| Production/customer-action release or causal dissatisfaction claim | **blocked** | The system is a human-review prioritization aid; inherited order reviews are weak labels and do not prove item causality. |

## Demo-only, non-confirmatory release scope

The current release boundary permits a documentation or UI walkthrough using
contracts, synthetic/fixture data, or explicitly labelled exploratory artifacts.
It may demonstrate navigation, schemas, API shape, workflow, and the intended
human-review queue. It must not be presented as a validated production model,
final benchmark, customer-impact result, or evidence that an item caused
dissatisfaction. A demo must display **demo-only / exploratory / not for
customer action** and must not substitute historical outputs for a sealed
evaluation.

## Claim and provenance rules

1. Every quantitative or empirical claim names its source artifact, run/status,
   data scope, and evaluation status. If no artifact supports it, do not state it.
2. Keep protocol, implementation status, development evidence, and confirmatory
   evidence separate. A checked checklist item is not a result.
3. Preserve qualifiers such as `exploratory_non_confirmatory`; do not relabel
   historical, development, synthetic, or demo outputs as final.
4. Cite the document or run artifact supporting a claim. Do not infer metrics,
   prevalence, confidence intervals, coverage, or business impact from code,
   screenshots, or a model file.
5. Describe item scores as risk prioritization under an inherited order-level
   review label. Do not claim item-level causation or automatic customer action.
6. Any later release claim must identify immutable data/manifests, code/config
   revision, split, artifact inventory, and validation status.

## Explicit P5 replacement-holdout gate

P5 cannot move from exploratory-only to confirmatory until a new evidence
artifact records all of the following:

- a genuinely untouched replacement holdout, independent of the disclosed
  historical final-test outputs and recovery rerun;
- a locked model, calibration, aggregation, wording, threshold, and evaluation
  configuration before that holdout is inspected;
- order-disjoint, time-valid lineage and immutable source/manifest references;
- the final evaluation outputs required by the modeling plan, including
  uncertainty and audit artifacts, with no post-hoc holdout selection; and
- review and sign-off that the evidence supports the proposed release claims.

Until that gate passes, confirmatory claims remain **blocked**. This document
records the boundary; it does not claim that a replacement holdout exists.

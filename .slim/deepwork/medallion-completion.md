# Medallion completion

## Goal

Complete the `feat/medallion` warehouse implementation only. Do not begin the
MLOPS/code-plan branch or modify `dev`.

## Accepted context

- `planning.md` requires Docker/PostgreSQL Bronze ingestion, dbt Silver/Gold,
  historical Bronze runs keyed by `source_run_id`, and reproducible lineage.
- Current feature commit `c0fc04b` provides a dbt Silver/Gold core but lacks
  run-scoped Bronze lineage and must be upgraded before it is considered
  complete.
- Oracle review: raw Bronze must be append-only per run; dbt must require one
  completed run and propagate `source_run_id` in every model and relationship.

## Delivery phases

1. Bronze run-scoped migration, loader contract, and focused tests.
   Gate: Oracle review of immutability, grants, and cutover safety.
2. dbt `source_run_id` enforcement and lineage propagation through Silver/Gold.
   Gate: Oracle review of mixed-run and grain risks.
3. Executable warehouse workflow and validation evidence.
   Gate: Oracle review of reproducibility and operational boundaries.

## Validation evidence

- Before code: design must preserve all nine raw sources and completed-run-only
  downstream selection.
- After phase 1: migration and loader tests against disposable PostgreSQL.
- After phase 2: `dbt build --vars source_run_id=...` plus lineage/cardinality
  checks.
- After phase 3: clean workflow/runbook evidence without touching MLOPS.

## Current state

- Branch: `feat/medallion`.
- Current worktree is clean.
- Phase 1 not started.

## Phase 1 accepted design

- New canonical Bronze schema is append-only by `source_run_id`; a rerun always
  creates a new run.
- The loader validates all nine files before any database mutation, holds one
  advisory lock, creates `STARTED`, loads all raw rows transactionally, then
  promotes the run to `COMPLETE`. On failure it records `FAILED` without raw
  rows.
- Legacy hash/truncate SQL is not an authoritative production path after this
  phase. No synthetic historical run will be fabricated from legacy tables.

## Phase 1 implementation evidence

- Changed paths: `infra/postgres/migrations/`, Bronze application and
  infrastructure modules, CLI ingestion wiring, and `tests/unit/test_bronze.py`.
- `uv run --frozen --extra db --extra dev pytest -q tests/unit`: 17 passed.
- Disposable database `hidden_dissatisfaction_bronze_phase1`: migration applied;
  two independent full canonical ingest runs are `COMPLETE`, each retains 99,441
  orders and 1,000,163 geolocation rows; two deliberately interrupted runs are
  `FAILED` and have no completed timestamp.
- Privilege evidence: `transform_runner` can SELECT Bronze;
  `app_runtime` cannot SELECT; `ingest_writer` cannot DELETE.

## Gate 1 review request

Review run-scoped immutability, transaction/lifecycle boundaries, manifest
validation, and role grants before any dbt lineage conversion.

## Gate 1 result — blocked

Oracle found terminal runs remain mutable at the database layer, raw tables do
not require a `STARTED` run on insert, grants/bootstrap are not reproducible,
and legacy cutover is undocumented. Remediation must add DB lifecycle guards,
strict insert-only run creation, role bootstrap/normalized grants, and a tested
blue/green cutover path. Structure scan additionally requires application ports
and shared Bronze contracts to be separated from adapters, plus CLI wiring
through a configuration/bootstrap boundary.

## Gate 1 remediation evidence

- Added role bootstrap, strict provenance/timestamp constraints, terminal-run
  lifecycle triggers, and raw insert guards in `infra/postgres/migrations/`.
- Moved application ports/contracts out of adapters and changed CLI wiring to
  use infrastructure database bootstrap.
- Final disposable-database rebuild applied migrations `000`–`003`, then ran
  two full canonical loads. Both runs are `COMPLETE`, have monotonic lifecycle
  timestamps, retain 198,882 order rows over two distinct `source_run_id`s,
  and cannot be terminally mutated or receive raw rows.
- Grant evidence remains: transform can read Bronze, app cannot, ingest cannot
  delete raw rows. Unit evidence: 17 passed.

## Gate 1 review attempt 2 — blocked

Remediation must make `STARTED` creation insert-only (no conflict update) and
normalize any pre-existing role grants by revoking all Bronze table privileges
before explicit least-privilege regrants. Structure scan also records follow-up
ports/CLI-test organization work, which does not block the database lifecycle
gate.

## Gate 1 final remediation evidence

- `STARTED` creation now uses a plain insert; UUID collision cannot reset a
  prior run.
- Grant migration was tested after deliberately granting legacy broad
  UPDATE/DELETE privileges: final transform/ingest update and delete checks are
  false, while transform read is true and app read is false.
- A clean disposable database applied migrations `000`–`003`; two full loads
  completed, preserve two historical order snapshots (198,882 rows), have
  monotonic complete timestamps, and DB negative checks reject terminal update
  and raw insertion into a completed run.

## Gate 1 final result

Approved by Oracle. Bronze lifecycle, grants, and blue/green cutover no longer
block dbt source-run lineage work. Phase 1 is an independently valid, currently
uncommitted delivery boundary; no commit is made without explicit user request.

## Phase 2 plan

- Lane A owns dbt project hooks/macros, Bronze sources, all Silver models and
  Silver tests. It must require one COMPLETE `source_run_id`, filter every
  source, and emit source lineage.
- Lane B owns only `dbt/models/gold/`; it must propagate lineage, use composite
  joins/grains, and retain payment/item measures separately.
- Validation will rebuild from a completed disposable Bronze run with
  `dbt build --vars source_run_id=...`, then test missing/invalid/non-complete
  variables. Oracle Gate 2 reviews mixed-run/cardinality risks.

## Phase 2 implementation evidence

- dbt requires a UUID `source_run_id` that resolves to one `COMPLETE` Bronze
  run before models execute; missing and unknown values both exit 2.
- Silver source models filter and propagate lineage; Gold joins, aggregations,
  dimensions, facts, bridges and marts use run-qualified composite grains.
- Full `dbt build` against a completed run passed 73/73. After a second
  historical Bronze load, rebuilding for the newer run produced exactly one
  Gold source run (99,441 orders) and zero independent order rollup mismatches.

## Gate 2 review request

Review mixed-run isolation, composite-key/cardinality correctness, and the
required-var execution boundary before operational workflow work begins.

## Gate 2 final result

Approved by Oracle. The COMPLETE-run execution boundary, Bronze filtering,
lineage propagation, run-qualified Gold joins/grains, and independent order
measure aggregation have no material isolation or fanout risk. Phase 3 may
implement the operational workflow contract.

## Phase 3 final evidence

- `dbt` is pinned to the 1.8 adapter line and exposed through reproducible
  Make targets. The profile is environment-only, secretless, and defaults to
  `hidden_dissatisfaction` while allowing overrides.
- `dbt parse` succeeds without a run var; execution still fails before models
  for a missing/malformed/non-COMPLETE run. The source-run freshness test reads
  ingestion metadata only, with an optional explicit maximum-age var.
- ADR-001 is accepted: canonical reviews select the latest answered review
  with deterministic tie-breaks and retain review multiplicity metadata.
- The full disposable-run build passed 89/89; `dbt docs generate` wrote its
  catalog artifact. Gold/Silver contracts include run-qualified relationships,
  canonical-review/cardinality/timestamp tests, descriptions, and API/ML
  exposures.
- Final Python gate passed Ruff, Black, strict Mypy, and pytest (18 passed;
  3 explicit skips for obsolete legacy-loader integration tests whose schema is
  intentionally absent from the canonical Bronze migration).
- Oracle approved Phase 3 with no material blockers. The Medallion Phase 1–3
  delivery remains uncommitted pending explicit user instruction.

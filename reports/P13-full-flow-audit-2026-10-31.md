# Full-flow audit — 2026-10-31

## Verdict

**Not release-ready.** The source establishes a substantial UI → API → workflow → PostgreSQL path, but the production frontend does not compile, live PostgreSQL verification could not run, API readiness is a stub, and the committed ML artifact does not load through the application artifact adapter.

## Current flow

```text
Angular frontend
  -> /api/v1 ApiClient
  -> FastAPI routes
  -> application workflow services
  -> PostgreSQL adapters and projections
  -> PostgreSQL app / bronze / silver / gold / ml schemas
  -> queue, order, decision, dashboard and audit UI

Olist CSVs
  -> bronze ingestion
  -> dbt silver / intermediate / gold
  -> gold.ml_modelling_items
  -> modelling export
  -> Python training / evaluation
  -> local joblib artifact + predictions
  -> release scoring / workflow queue
```

Primary references: `compose.yaml`, `src/hidden_dissatisfaction/api/app.py`, `src/hidden_dissatisfaction/api/workflow_routes.py`, `frontend/hidden-dissatisfaction-frontend/src/app/core/api-client.service.ts`, `docs/local-development.md`, and `.github/workflows/quality.yml`.

## UI ↔ backend integration

| Workflow | Status | Evidence |
|---|---|---|
| Login, session and language | Connected, with error-state gaps | `api-client.service.ts`, `auth.store.ts`, `api/app.py` |
| Queue, filters, pagination and claim | Connected | `queue.store.ts`, `api/app.py` |
| Order detail and workflow mutations | Connected | `order-actions.facade.ts`, `workflow_routes.py` |
| Evidence upload and contact attempts | Connected | `attempt.facade.ts`, `workflow_routes.py` |
| Manager decisions, dashboard, parameters, audit | Connected | feature facades/components and corresponding API routes |
| `web/Wireframe` | Disconnected prototype | Static HTML/JS uses `mock-data.js` |

### Contract defects

1. **`GET /users` response mismatch — high.** The API returns `{ "items": [...] }` (`api/app.py`), while `ApiClient.users()` is typed and consumed as `UserDto[]`. Assignee selection and manager decisions can fail at runtime.
2. **Comment/model-note response mismatch — medium.** Frontend DTOs expect wrapped responses, but workflow routes return direct command results. Callers currently ignore the response, so this is latent contract drift.
3. **Structured login errors are not rendered — low.** The UI reads `error.message` rather than the API error envelope.
4. **Frontend compilation failure — blocking.** No browser UI can be released until Angular errors are corrected (see verification).

## Database assessment

### What is present

- Compose defines PostgreSQL, migration, API, frontend, test frontend and warehouse services.
- Forward-only migrations and init scripts exist under `infra/postgres/`.
- CI defines PostgreSQL integration gates for ingestion, release scoring, parameters and workflow behavior.
- Static configuration validation passed: `docker compose --env-file .env.example config --quiet` and shell syntax checks on migration/init scripts.

### What is not established

- No `.env`, configured Compose stack, running PostgreSQL service, or DSN was available in this workspace.
- Therefore **20 PostgreSQL integration tests were skipped** and real migration/repository/database stability is unproven.
- `/health/ready` is not a database readiness check: `readiness_check()` always returns `True`. A 200 response cannot establish database connectivity or migration state.

## ML assessment

### Evidence

- Focused modeling/repository tests: **20 passed**.
- Raw joblib artifact loads as `CalibratedClassifierCV`.
- Inference works for a 165-feature input: `predict_proba` returned `(1, 2)`.
- Application envelope loading **fails**: `ModelArtifactError: model artifact must be an envelope`.

### Risks

- The deliverable artifact and `JoblibModelArtifact` adapter contract are incompatible; the production scoring path is not proven loadable.
- Repository documentation declares product-item scoring authoritative, while portions of Python training/historical artifacts remain order-level. This is a data-grain contract risk.
- Artifacts are local/ignored rather than versioned in a registry; reproducible deployment and rollback are not established.

## Verification evidence

| Command/check | Result | Interpretation |
|---|---:|---|
| `uv run pytest tests/unit tests/contract -q` | PASS — 162 passed, 3 skipped | Backend unit/contract behavior currently covered |
| `uv run pytest tests/integration -q` | PARTIAL — 1 passed, 20 skipped | Database-dependent behavior not verified |
| Focused model/repository tests | PASS — 20 passed | Local model/repository logic covered |
| ML load/inference probe | PARTIAL | Raw model works; production envelope loader fails |
| `python -m compileall -q src tests` | PASS | Python syntax/import compilation passed |
| `npm run lint` | PASS | Frontend lint passed |
| `npm test` | FAIL | Angular compile errors prevented all browser tests |
| `npm run build` | FAIL | Production frontend cannot build |
| Compose config with `.env.example` | PASS | Template is structurally valid |
| Live Compose/PostgreSQL smoke test | BLOCKED | `.env` and running stack unavailable |

Frontend compiler blockers include `withXhr` not exported by `@angular/common/http` and invalid `ChangeDetectionStrategy.Eager` references. No frontend test specifically detects the `/users` response-shape defect.

## Required remediation order

1. Fix Angular dependency/API usage (`withXhr`, `ChangeDetectionStrategy.Eager`), then rerun frontend lint, test and build.
2. Align `/users`, comment and model-note API DTOs; add contract tests that exercise client response mapping.
3. Provide a non-secret local `.env`/test DSN, bring up Compose PostgreSQL, run migrations and the skipped integration suite.
4. Replace stub readiness with a bounded database connectivity and migration-state check.
5. Standardize the ML artifact envelope (or adapter) and add a release-scoring smoke test that loads the deployed artifact.
6. Resolve and document the authoritative model grain (product-item vs order) before retraining/scoring release.

## Limits

This audit did not alter source, lockfiles, database state or Compose volumes. Full warehouse/dbt P4 release verification was not run because its required credentials and source-run data were unavailable.

## Disposition note

This dated audit is retained unchanged as historical evidence. The static frontend cutover is now
delivered under `frontend/prototype`; the audit's browser/build and live-stack findings remain its
original status, and no browser E2E coverage is claimed for the cutover.

# Prototype backend migration

## Goal

Make `web/Prototype` the sole delivered frontend and align FastAPI, delivery infrastructure, and verification with its real (non-mock) contract.

## Accepted context

- Final candidate: `web/Prototype`, imported from `origin/main` at `1445ce7`.
- Existing Angular delivery is currently wired through `compose.yaml`, its Dockerfile/nginx config, CI, and smoke tests.
- Prototype API contract and backend comparison: `web/Prototype/{README.md,BACKEND.md,js/api.js,js/config.js}`; `src/hidden_dissatisfaction/api/{app.py,workflow_routes.py,schemas.py}`.
- Architecture assessment: Oracle lane `ora-1`; dependency map: explorer lane `exp-6`.

## Accepted decision

- User approved full replacement of the Angular frontend by `web/Prototype`.
- Implementation remains phased: Phase 1 establishes a real, authenticated queue/detail/claim/close contract; unsupported screens are removed from the delivered UI rather than left as mock-backed controls.
- Accepted Phase 1 contract: Oracle lane `ora-1`; projection evidence: explorer lane `exp-7`.

## Proposed phases and gates

1. Contract/security alignment — FastAPI DTOs/auth/projections + API tests. Gate: Oracle review, unit/contract/integration tests.
2. Prototype hardening and delivery — serve only non-mock static UI through Nginx, same-origin API, safe rendering. Gate: Oracle review, static delivery and browser/contract tests.
3. Cutover/deprecation — update Compose/CI/docs/smoke tests and remove or archive Angular only if approved. Gate: Oracle review, full Compose E2E and rollback check.

## Phase 1 execution

- Owner: `@fixer`, scope limited to FastAPI public DTOs, queue/detail read projections, authorization, and tests.
- Backend retains `/auth/me` as the canonical profile route; Prototype is adapted in Phase 2 instead of adding a permanent `/me` alias.
- Public API must return `risk_score` / `risk_level`, a rich queue response, explicit principal workload fields, and authenticated operational reads.
- Validation: focused Python tests plus contract tests; PostgreSQL integration evidence when local stack is available.

## Phase 1 implementation evidence

- Changed: `src/hidden_dissatisfaction/api/{app.py,schemas.py}`, `application/queue.py`, and `infrastructure/postgres_risk_queue.py`.
- Implemented: auth on orders/filter options, HTTP resolution of `assignee=me`, `risk_score`/`risk_level` queue naming, queue pagination, richer queue mapping, and principal workload fields.
- Local validation: `python -m compileall -q src/hidden_dissatisfaction`; `uv run pytest tests/unit tests/contract -q` → 162 passed, 3 skipped.
- Outstanding before gate: inspect whether the queue/detail data mapping meets the approved Phase 1 shape, and add contract coverage for the new behavior if absent.

## Phase 1 gate — attempt 1

- Result: **blocked** by Oracle review.
- Accepted corrections: queue projection must populate typed top-item/workflow/metric fields; detail needs a typed public schema and explicit mapping; principal/summary workload normalization needs a dedicated path; and readiness must check database/migration state.
- Tests must cover protected reads, `assignee=me`, rich queue/detail shapes, workload normalization, workflow return DTOs, and real PostgreSQL fixtures.
- Remediation owner: `@fixer`; then rerun focused/broad tests and request Oracle re-review attempt 2 of 3.

## Phase 1 remediation status

- Partial remediation added typed queue/support schemas, timestamp/pagination plumbing, improved assignee naming, and readiness connectivity/migration-table checks.
- Still incomplete: full rich queue SQL/mapper and shared metrics mapping, typed detail response/mapping, direct principal workload projection, and contract coverage for these paths.
- Continue remediation before Oracle re-review; do not start Phase 2.

## Phase 1 remediation escalation

- A second implementation pass stopped rather than fabricate SQL fields. It only added a `case_metrics` import; no rich queue/detail mapping or new coverage was delivered.
- Before retrying, obtain an exact source-to-SQL/DTO mapping from the architecture lane and split the next implementation into bounded queue/detail and principal/readiness/test lanes if their file scopes do not overlap.

## Phase 1 completed remediation evidence

- DTO contract was tightened; queue, detail, and principal/readiness lanes were implemented and an API integration repair aligned application DTOs with public schemas.
- Added migration `V021__api_readiness_ledger_grant.sql`; migrated local PostgreSQL applied it successfully.
- Live Compose evidence after API rebuild: readiness 200; anonymous config 401; authenticated queue 200 with `items,total,limit,offset`; summary 200; and detail 200 with `order,status_history,seller_open_count`.
- `uv run pytest tests/unit tests/contract -q` → 162 passed, 3 skipped after final source changes. The plain integration suite timed out after reporting 20 skips; live migrated-stack validation is retained as boundary evidence.
- Request Oracle Phase 1 gate re-review attempt 2 of 3 before Phase 2 begins.

## Phase 1 gate — attempt 2

- Result: **blocked**. The strict DTO boundary exposed that queue top items were still null and detail mapping had removed fields used by the Prototype core order page.
- Required remediation: populate top-item/original-queue data from existing risk views; restore a single explicit typed detail DTO covering existing items, cycle/contact/comment/decision/audit payloads required by `order.html`; repair contradictory route/integration fixtures; add HTTP-level PostgreSQL contract tests.
- This is the final remediation pass before the last Oracle re-review (attempt 3 of 3).

## Phase 1 final remediation evidence

- Queue projection now maps a real top item from the persisted top-product item, including category/data source/factors, and preserves separate current/original queue timestamps.
- Detail mapping restores explicit typed workflow collections and maps top-item category/data source required by the core order page.
- Live Compose validation: readiness 200; anonymous configuration/orders/filter-options 401; authenticated queue 200 with four typed items and non-null top items; summary 200; queue-derived detail 200 with core workflow/detail fields.
- Final local quality evidence: `uv run pytest tests/unit tests/contract -q` → 162 passed, 3 skipped; `git diff --check` passed.
- Request final Phase 1 Oracle gate review attempt 3 of 3.

## Phase 1 gate — attempt 3

- Result: blocked because the core detail contract remains shallow: the DTO defaults permit 200 responses that omit items and workflow collections required by `order.html`.
- User explicitly authorized one exceptional, narrow remediation beyond the planned review budget: restore the full typed detail DTO/mapper and prove it with HTTP/PostgreSQL tests.
- No Phase 2 work may begin until this remediation has independent validation and a focused final review.

## Exceptional detail remediation evidence

- Full detail mapper now returns the required workflow collections and typed item/model metadata; strict schemas were aligned to the authoritative projection.
- Final live verification after a no-cache API build: login 200, queue 200, queue-derived detail 200 with all core sections and nested metadata.
- `uv run pytest tests/unit tests/contract -q` → 163 passed, 3 skipped.
- Request one focused exceptional Oracle confirmation limited to the resolved detail contract before Phase 2 begins.

## Phase 1 accepted

- The route fixture was updated to the full strict detail contract; the negative missing-collection assertion was added.
- `uv run pytest tests/unit tests/contract -q` → 163 passed, 3 skipped after the fixture update.
- Phase 2 may now begin: replace Angular delivery with the real-mode Prototype, preserving its approved visual/interaction design while removing mock/demo runtime paths.

## Phase 2 delivery evidence

- `frontend/prototype/` now contains the approved Prototype visual design in real same-origin API mode with mock/demo/API-check runtime removed and safe string rendering added.
- Compose/CI/static checks now build and serve `frontend/prototype`; the Angular directory remains temporarily as an unserved rollback artifact.
- A first live proxy check found variable-upstream DNS failure; it was corrected to the Docker service upstream.
- Final local delivery evidence: frontend/API healthy; root redirects to login; static screens return 200; same-origin login, queue, and queue-derived detail return 200; `tests/static-quality.sh` and `tests/smoke.sh` pass.
- Request Phase 2 Oracle gate before Phase 3 removal of the unserved Angular rollback artifact.

## Phase 2 gate remediation

- Static/CI smoke assertions now match the fixed Docker service proxy and verify unauthenticated same-origin API behavior.
- Prototype real-mode rendering now escapes API/user-derived strings, validates dynamic URLs, and has a security regression check.
- Unsupported order/customer/product fields were removed from the delivered UI; supported fields remain.
- Final local delivery evidence: `git diff --check`, `tests/static-quality.sh`, `node frontend/prototype/security-regression-check.js`, Compose rebuild, and `tests/smoke.sh` all pass.
- Request Phase 2 Oracle re-review attempt 2 of 3.

## Phase 2 XSS remediation

- All identified dynamic rendering sinks across the delivered Prototype were converted to context-safe rendering; regression payloads now cover the repaired screens and unsafe URLs.
- The security regression check is now a required CI static-quality step.
- Final local evidence after this remediation: static quality/security checks, Compose build, and same-origin smoke all pass.
- Request Phase 2 Oracle re-review attempt 3 of 3 before deleting the rollback artifact.

## Phase 2 gate — attempt 3

- Result: blocked by remaining raw dynamic interpolation and an insufficient regression test.
- User explicitly authorized one exceptional final XSS remediation: remove/escape each remaining sink and test the delivered render paths with malicious payloads before considering Angular removal.

## Exceptional Phase 2 XSS remediation evidence

- Remaining raw interpolation sites were removed or context-escaped across delivered screens; dynamic identifiers and URLs are encoded/validated.
- The regression check now covers delivered render/sink patterns with malicious text and unsafe URL payloads; CI executes it.
- Final local evidence: `git diff --check`, static quality, security regression, Compose build, and same-origin smoke all pass.
- Request exceptional focused Oracle confirmation before Phase 3 deletion.

## Final inline-handler remediation

- Exceptional confirmation found one remaining JavaScript-string context escape defect in the delivered item handler.
- User approved one final narrow correction: replace the inline handler with a data-attribute/event binding and prove the actual renderer safe.

## Final inline-handler evidence

- The product item inline handler was replaced by a data attribute and bound click/Enter events; regression fixtures cover apostrophes, markup, and unsafe URL-shaped values in the delivered renderer.
- Final local evidence remains green: diff check, static quality, security regression, Compose build, and same-origin smoke.
- Request final exceptional Oracle confirmation for Angular removal.

## Phase 3 completion

- Oracle granted final approval for Angular removal after the data-attribute/event-binding XSS remediation.
- Removed `frontend/hidden-dissatisfaction-frontend/` and its active repository references; the only retained mention is a historically accurate audit report.
- Final delivery gate passed: diff check, static Prototype check, security regression, Compose frontend build, same-origin smoke, and `163 passed, 3 skipped` unit/contract tests.

## Non-negotiable checks

- Auth required for all case/configuration reads.
- Prototype mock/demo runtime excluded from production image.
- `/health/ready` validates DB/migration state.
- Contract fixtures cover queue/detail/config/profile/parameters/dashboard/audit shapes.
- No destructive database migration or frontend deletion without a valid rollback path.

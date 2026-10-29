# P11 runtime gate — 2026-10-29

Status: **Compose E2E and authenticated synthetic walkthrough passed**

## Passed gates

- `scripts/release-check.sh`: passed.
- Ruff: passed.
- Black: passed.
- Mypy: passed.
- Python unit and API contract suite: **197 passed**.
- Frontend ESLint: passed.
- Frontend production build: passed after the Angular 22 upgrade; initial bundle `371.36 kB` raw / `102.58 kB` estimated
  transfer, below the configured budget.
- Frontend Karma/Jasmine suite: **17 passed** in containerized Chromium Headless.
- Docker Compose migrations: passed against the healthy PostgreSQL service.
- API container: healthy.
- Frontend container: healthy.
- `make e2e`: passed, including synthetic marker and API/frontend smoke checks.
- Authenticated synthetic demo walkthrough: passed. The local seed creates or
  refreshes a Specialist using an Argon2 hash; login plus orders, queue summary,
  filter options, and users all returned successfully. Credentials live only in
  the owner-readable, Git-ignored `data/evidence/P12-DEMO-CREDENTIALS.env`.

During the gate, the unconstrained FastAPI dependency resolved to a new major-compatible but
test-incompatible stack. The project now pins FastAPI to `>=0.115,<0.116`; API uses the stable
Starlette 422 status constant. The lockfile was regenerated and the Python suite passed afterward.

## Runtime repairs made during the gate

- Used a temporary Docker client config for public image pulls because the configured Windows
  credential helper was unavailable while WSL interop returned `UtilAcceptVsock ... accept4 failed
  110`. User credentials and the persistent Docker config were not modified.
- Added the `db` dependency extra to the API image; the application composition root imports
  PostgreSQL adapters and therefore requires `psycopg` at runtime.
- Updated the frontend smoke probe to recognize the actual Angular root selector (`hd-root`) and
  retry readiness, removing the immediate-start race.

### Frontend component execution

The unsupported Karma/jsdom combination connected but could not execute the ESM test bundle. It was
replaced with Karma/Jasmine on containerized Chromium Headless. A dedicated `frontend-test` Compose
profile and `make frontend-test` target now provide a reproducible browser environment. The first
real execution exposed two stale test fixtures; both were corrected, and all 17 specs passed.

## Remaining quality work

The post-upgrade `npm audit --json` has zero reported vulnerabilities. The core P11 Compose/runtime
gate and P10 frontend test execution gate are complete for the authenticated synthetic demo scope.

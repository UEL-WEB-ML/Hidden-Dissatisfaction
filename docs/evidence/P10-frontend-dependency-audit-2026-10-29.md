# P10 frontend dependency audit — 2026-10-29

Status: **resolved by the approved Angular 22 upgrade**

## Evidence

The initial `npm audit --json` reported 54 findings: 7 low, 19 moderate, 26 high, and 2 critical.
The two critical build-time transitive dependencies were:

- `piscina@4.6.1`, introduced by Angular build tooling; advisories require `>=4.9.4`.
- `tar@6.2.1`, introduced through Angular CLI's package tooling; current advisories require a 7.x
  release.

The production dependencies were also affected by Angular XSS advisories. Angular 18 had no
supported non-major remediation; the audit's fix path required Angular 20–22.

## Remediation completed

- Performed the official sequential framework/CLI migrations from Angular 18 through 22 rather
  than applying `npm audit fix --force` or untested transitive overrides.
- Current framework is Angular `22.2.3`; CLI/build tooling is `22.2.5`; TypeScript is `6.0.3`.
- Updated the production frontend image from Node 22 to Node 24 to meet the supported runtime
  range of the upgraded framework.
- Final `npm audit --json` result: **0 vulnerabilities** (0 critical, 0 high, 0 moderate, 0 low).
- Regression evidence: ESLint and production build passed; 17/17 Chromium Headless specs passed;
  production Compose rebuild and `make e2e` passed.

## Remaining maintenance item

The Angular legacy Karma/Webpack builder emits a deprecation warning. It has no current `npm audit`
finding and does not block this release; migrate the test builder to Vitest in a separately scoped
change so its test semantics can be reviewed independently.

## Disposition note

This dated audit is retained as original evidence. The completed static frontend cutover is delivered
under `frontend/prototype`; this record does not establish browser E2E coverage for that path.

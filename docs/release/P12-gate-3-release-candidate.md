# P12 Gate 3 release-candidate checklist

Version: `0.1.0-demo.3`. Scope is application and synthetic demo only;
exploratory ML evidence remains development evidence.

- [ ] `make release-check` passes from a clean checkout.
- [ ] Python quality/tests and frontend lint/build pass where available.
- [ ] Compose parses with `.env` values and exposes localhost only.
- [ ] Migration completion and API/frontend health dependencies remain explicit.
- [ ] `make e2e` passes, or unavailable credentials/services are recorded as skips.
- [ ] No raw Olist files, secrets, credentials, or generated evidence are tracked.
- [ ] Demo artifacts are labelled synthetic and include command, revision, and date.
- [ ] Exploratory reports are not presented as confirmatory performance.

Record release-check output, `git status --short`, tool versions, and skipped
runtime gates. Never commit `.env`, raw data, tokens, or customer screenshots.

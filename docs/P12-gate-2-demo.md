# P12 Gate 2 demo runbook

This is a synthetic, deterministic product walkthrough. It is not a full Olist
load, a model release, or confirmatory ML evidence.

## Run

```text
cp .env.example .env
make app-up
make e2e
```

`make e2e` probes API live/readiness, the frontend shell, and writes a clearly
labelled `data/evidence/P12-SYNTHETIC.txt` marker. On its first local run, it
generates random Specialist and Manager credentials in the Git-ignored,
owner-readable `data/evidence/P12-DEMO-CREDENTIALS.env`. You may instead set
both `DEMO_USERNAME` and `DEMO_PASSWORD` in the ignored local `.env`. The seed
step creates or refreshes both accounts with Argon2 password hashes, an
explicitly `SYNTHETIC_DEMO` active prediction snapshot, five synthetic cases,
and a small amount of workflow history. The walkthrough exercises Specialist
queue/summary/filter/user APIs and Manager config/parameters/dashboard/audit
APIs. Specialist claim/case actions can be demonstrated
manually with that account; the script never creates Olist rows or mutates
production data.

## Capture fallback

Preferred: record the browser walkthrough with Playwright/OBS. Fallback:
capture terminal output from `make e2e`, `docker compose ps`, and browser
screenshots of `/health`, queue, case workflow, audit, parameters, and dashboard.
Name artifacts `P12-gate-2-<date>-synthetic.*`; retain the command, git revision,
environment, and explicit skipped checks beside them. Never include real
customer data or claim performance from this fixture.

## Defense Q&A

- **Leakage?** Features stop at delivery confirmation; review labels are never
  available at prediction time. The review is an order-level weak label copied
  to items, not an item causal label.
- **Weak labels?** An item inherits its order review outcome; use this for
  prioritization, not attribution, and disclose label noise.
- **Calibration?** Calibration is a release gate to be measured on a temporal,
  order-clustered holdout; this demo does not establish calibration.
- **Why max-v1?** It is the transparent initial order aggregation: the highest
  item risk prioritizes an order for human review and is versioned for replacement.
- **Business value?** Rank limited specialist capacity toward potentially
  dissatisfied orders; no automatic customer action is taken.
- **Causal limitations?** Scores identify risk association only. They do not
  prove which item caused dissatisfaction or that intervention changes outcomes.

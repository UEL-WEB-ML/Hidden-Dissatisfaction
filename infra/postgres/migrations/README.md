# PostgreSQL migrations

Migrations are forward-only and are executed by `make migrate` after the
bootstrap scripts. The runner connects as the configured PostgreSQL superuser,
records successfully applied filenames in `app.schema_migrations`, and is safe
to rerun. Migrations use `SET ROLE
hidden_dissatisfaction_owner` for DDL, then resets role before grants (the
bootstrap `migrator` role is NOLOGIN). It does not baseline, inspect, or
alter existing application tables. Apply it explicitly to an isolated local
database, for example:

```text
createdb --username=postgres hidden_dissatisfaction_p61_test
psql --username=postgres --file infra/postgres/init/00-roles-and-schemas.sql hidden_dissatisfaction_p61_test
psql --username=postgres --file infra/postgres/migrations/V001__p6_1_prediction_contract.sql hidden_dissatisfaction_p61_test
psql --username=postgres --file tests/sql/p6_1_contract.sql hidden_dissatisfaction_p61_test
dropdb hidden_dissatisfaction_p61_test
```

The runner never auto-baselines an existing database: a database that already
contains tables but has no `app.schema_migrations` ledger must be migrated only
after an explicit operator review.

## P9 migrations

| Version | Purpose |
|---|---|
| V009-V011 | Runtime language grant, parameter grants, initial parameter bundle |
| V012 | Workflow contract columns (attempt, decision) |
| V013 | `attempt_no` unique per cycle; `evidence_uploads` for unattached files |
| V014 | `p7_case_guard` runs as definer so runtime updates pass the snapshot guard |
| V015 | Read-path indexes chosen from `EXPLAIN ANALYZE` on about 100k cases |
| V016 | `ml.v_active_thresholds` so `/config` needs no raw `ml.*` grant |
| V017 | `app.sla_adjustments` (append-only) for recalculated open-cycle SLA |
| V018 | Retention purge of unattached uploads; attached evidence stays protected |
| V019 | Bronze raw CSV tables and run-scoped ingestion contract |
| V020 | Explicit synthetic-demo release status and prediction state transitions |
| V021 | Runtime read grant for the migration ledger readiness check |
| V022 | Historical case prediction visibility and least-privilege queue seeding view |

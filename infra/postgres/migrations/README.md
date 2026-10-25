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

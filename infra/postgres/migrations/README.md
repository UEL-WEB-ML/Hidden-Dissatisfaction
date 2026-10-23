# PostgreSQL migrations

`V001__p6_1_prediction_contract.sql` is forward-only and should be executed by
a superuser after the bootstrap scripts. It uses `SET ROLE
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

The migration is intentionally not wired into container startup. This prevents
an existing production-like volume from being changed unintentionally. A later
runner may record applied filenames in a dedicated migration ledger; it must
not auto-baseline an existing database.

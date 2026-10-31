# Label/snapshot build-log evidence

The available dbt log is `dbt/logs/dbt.log`; it is not copied here because it is a 3.9 MB operational log. It records this completed rebuild of the retained modeling snapshot:

- dbt version: 1.8.10.
- dbt build invocation used source run ID `6f13bf55-5ce3-4a58-807e-e1c31ff76eaa`.
- Intermediate interaction table, which is joined from `int_p4_cohort`, returned `SELECT 97884`.
- Gold `ml_modelling_items` was built from `int_p4_cohort` and returned `SELECT 97884` in 2.912 seconds; dbt reports it as successfully created in 2.96 seconds.
- The subsequent row-grain and uniqueness checks passed.

This proves the 97,884-item snapshot build, but the log has no per-stage counts for all orders, delivered orders, on-time orders, or observed-review orders. It therefore cannot explain the five-order / six-item difference between the current raw-file re-derivation (85,420 orders / 97,878 items) and the retained snapshot (85,425 / 97,884).

Suggested thesis note: “The archived dbt execution log verifies successful materialization of 97,884 item rows and post-build row-grain checks, but it does not retain a stage-wise cohort-count audit. A later re-derivation from the available raw CSV snapshot differed by five orders and six items; we therefore report the frozen snapshot counts for modeling and treat the raw re-derivation as a non-identical audit.”

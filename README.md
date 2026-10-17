# Bronze ingestion

Apply the versioned migration (from `Docker_Environment`):

```text
docker compose --env-file ~/.config/docker-environment/.env exec -T postgres psql -U postgres -d ironman -v ON_ERROR_STOP=1 -f /sql/migrations/001_bronze.sql
```

Then run the stdlib-only loader from this directory:

```text
python scripts/load_bronze.py [--env-file /path/to/.env]
```

The loader validates all nine canonical files and their manifest checksums before taking an advisory lock and loading one run. It preserves historical runs and performs no Silver/Gold transformations.

## Silver

Create a virtualenv and install matching pinned packages: `python -m pip install 'dbt-core==1.8.2' 'dbt-postgres==1.8.2'`. Then run `python scripts/build_silver.py [--env-file PATH] [--run-id UUID] [--dbt-bin PATH]`. The default selects the latest completed Bronze run and passes exactly one `source_run_id` dbt variable. Validate without building with `dbt parse --project-dir dbt --profiles-dir dbt`.

The runner also builds the available Gold core: historical dimensions, order/item/payment facts, distinct order bridges, safe delivery views, and Olist-only aggregates. `dim_ml_feature` is intentionally empty; risk, SLA, workload, contact, and app workflow inputs require a separately approved contract. Direct selection: `dbt build --project-dir dbt --profiles-dir dbt --vars '{source_run_id: "UUID"}'`.

select run_id source_run_id, manifest_sha256, started_at, completed_at from {{ source('bronze','ingestion_runs') }} where status='complete' and run_id='{{ var("source_run_id") }}'::uuid

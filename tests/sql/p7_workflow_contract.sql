\set ON_ERROR_STOP on
-- Structural contract checks; run after V001..V007 in an isolated database.
DO $$ BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='assignments_one_active_per_case') THEN RAISE EXCEPTION 'missing active assignment constraint'; END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='audit_actor_kind_fk') THEN RAISE EXCEPTION 'missing audit actor constraint'; END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='audit_queue_seed_kind_ck') THEN RAISE EXCEPTION 'missing queue seed constraint'; END IF;
 IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='app' AND table_name='contact_evidence' AND column_name='metadata') THEN RAISE EXCEPTION 'missing evidence metadata'; END IF;
END $$;
SELECT has_table_privilege('app_runtime','app.assignments','SELECT') AS assignments_select;
SELECT has_table_privilege('app_runtime','app.audit_events','INSERT') AS audit_insert;
SELECT has_table_privilege('app_runtime','app.parameters','UPDATE') AS parameters_update;

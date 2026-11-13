\set ON_ERROR_STOP on
DO $$ BEGIN
 IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='parameter_bundles_revision_idx') THEN RAISE EXCEPTION 'bundle revision is incorrectly unique'; END IF;
 IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='app' AND table_name='review_cycles' AND column_name='parameter_bundle_id') THEN RAISE EXCEPTION 'cycle bundle reference missing'; END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='review_cycles_one_open_per_case') THEN RAISE EXCEPTION 'open cycle constraint missing'; END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE pronamespace='app'::regnamespace AND proname='close_review_cycle') THEN RAISE EXCEPTION 'controlled closure missing'; END IF;
END $$;

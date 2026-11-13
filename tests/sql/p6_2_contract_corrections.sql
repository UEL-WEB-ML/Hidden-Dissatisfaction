\set ON_ERROR_STOP on
BEGIN;
DO $$
DECLARE v numeric; s text; c boolean;
BEGIN
  SELECT numeric_scale INTO v FROM information_schema.columns
   WHERE table_schema='ml' AND table_name='model_thresholds' AND column_name='high_from';
  IF v <> 17 THEN RAISE EXCEPTION 'threshold precision not corrected'; END IF;
  SELECT is_nullable='NO' INTO c FROM information_schema.columns
   WHERE table_schema='ml' AND table_name='model_thresholds' AND column_name='selection_policy';
  IF NOT c THEN RAISE EXCEPTION 'selection_policy is nullable'; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='predictions_input_hash_sha256_ck')
     OR NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='predictions_model_input_hash_sha256_ck')
  THEN RAISE EXCEPTION 'hash checks missing'; END IF;
END $$;
DO $$ BEGIN
  BEGIN
    INSERT INTO ml.predictions(prediction_id,model_release_id,threshold_version,source_run_id,input_hash,model_input_hash,scored_at,state)
    VALUES ('10000000-0000-0000-0000-000000000099','00000000-0000-0000-0000-000000000002','1','20000000-0000-0000-0000-000000000099','bad',repeat('a',64),now(),'READY');
    RAISE EXCEPTION 'invalid hash accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
END $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='ml' AND table_name='v_risk_orders_for_web' AND column_name IN ('aggregation_rule','items_count','predicted_at'))
  THEN RAISE EXCEPTION 'corrected order view fields missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='ml' AND table_name='v_risk_items_for_web' AND column_name IN ('aggregation_rule','predicted_at','model_release_id','threshold_version'))
  THEN RAISE EXCEPTION 'corrected item view fields missing'; END IF;
END $$;
ROLLBACK;

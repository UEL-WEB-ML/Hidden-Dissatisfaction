\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- A synthetic walkthrough must never be labelled as a confirmatory model
-- release. This explicit state is usable only for locally seeded demo snapshots.
ALTER TABLE ml.model_releases
  DROP CONSTRAINT model_releases_evaluation_status_check,
  ADD CONSTRAINT model_releases_evaluation_status_check
    CHECK (evaluation_status IN ('EXPLORATORY_NON_CONFIRMATORY', 'CONFIRMATORY', 'SYNTHETIC_DEMO'));

CREATE OR REPLACE FUNCTION ml.prediction_state_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE evaluation text;
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'predictions are immutable'; END IF;
  SELECT evaluation_status INTO evaluation
    FROM ml.model_releases WHERE model_release_id = NEW.model_release_id;
  IF TG_OP = 'INSERT' AND NEW.state = 'ACTIVE'
     AND evaluation NOT IN ('CONFIRMATORY', 'SYNTHETIC_DEMO') THEN
    RAISE EXCEPTION 'only confirmatory or explicitly synthetic-demo releases may be ACTIVE';
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF NEW.prediction_id<>OLD.prediction_id OR NEW.model_release_id<>OLD.model_release_id
       OR NEW.threshold_version<>OLD.threshold_version OR NEW.source_run_id<>OLD.source_run_id
       OR NEW.input_hash<>OLD.input_hash OR NEW.model_input_hash<>OLD.model_input_hash
       OR NEW.scored_at<>OLD.scored_at OR NEW.created_at<>OLD.created_at THEN
      RAISE EXCEPTION 'prediction snapshot is immutable';
    END IF;
    IF NOT ((OLD.state='READY' AND NEW.state IN ('ACTIVE','REJECTED'))
            OR (OLD.state='ACTIVE' AND NEW.state='SUPERSEDED')) THEN
      RAISE EXCEPTION 'invalid prediction state transition';
    END IF;
    IF NEW.state='ACTIVE' AND evaluation NOT IN ('CONFIRMATORY', 'SYNTHETIC_DEMO') THEN
      RAISE EXCEPTION 'only confirmatory or explicitly synthetic-demo releases may be ACTIVE';
    END IF;
  END IF;
  IF NEW.state='ACTIVE' AND NEW.activated_at IS NULL THEN NEW.activated_at := now(); END IF;
  RETURN NEW;
END;
$$;

RESET ROLE;

\set ON_ERROR_STOP on

-- Run as migrator.  Ownership is deliberately held by the owner role.
SET ROLE hidden_dissatisfaction_owner;

CREATE TABLE ml.model_releases (
  model_release_id uuid PRIMARY KEY,
  release_version text NOT NULL UNIQUE,
  model_name text NOT NULL, model_version text NOT NULL, model_artifact_uri text NOT NULL,
  artifact_sha256 text NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-fA-F]{64}$'),
  feature_schema_version text NOT NULL,
  dataset_manifest_sha256 text NOT NULL CHECK (dataset_manifest_sha256 ~ '^[0-9a-fA-F]{64}$'),
  training_git_sha text NOT NULL, source_snapshot_hash text NOT NULL,
  training_run_id uuid NOT NULL,
  aggregation_rule text NOT NULL CHECK (aggregation_rule = 'max-v1'),
  evaluation_status text NOT NULL CHECK (evaluation_status IN ('EXPLORATORY_NON_CONFIRMATORY','CONFIRMATORY')),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ml.model_thresholds (
  model_release_id uuid NOT NULL REFERENCES ml.model_releases,
  threshold_version text NOT NULL,
  medium_from numeric(12,10) NOT NULL CHECK (medium_from >= 0 AND medium_from <= 1),
  high_from numeric(12,10) NOT NULL CHECK (high_from >= 0 AND high_from <= 1 AND high_from > medium_from),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (model_release_id, threshold_version)
);
CREATE TABLE ml.predictions (
  prediction_id uuid PRIMARY KEY, model_release_id uuid NOT NULL,
  threshold_version text NOT NULL, source_run_id uuid NOT NULL,
  input_hash text NOT NULL, model_input_hash text NOT NULL, scored_at timestamptz NOT NULL,
  state text NOT NULL CHECK (state IN ('READY','ACTIVE','SUPERSEDED','REJECTED')),
  created_at timestamptz NOT NULL DEFAULT now(), activated_at timestamptz,
  FOREIGN KEY (model_release_id, threshold_version) REFERENCES ml.model_thresholds
);
CREATE UNIQUE INDEX predictions_one_active ON ml.predictions ((state)) WHERE state = 'ACTIVE';

CREATE TABLE ml.item_prediction_scores (
  prediction_id uuid NOT NULL REFERENCES ml.predictions,
  order_id text NOT NULL, order_item_id text NOT NULL, product_item_id text NOT NULL,
  score numeric(12,10) NOT NULL CHECK (score >= 0 AND score <= 1),
  risk_context jsonb NOT NULL DEFAULT '{}'::jsonb, top_factors jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(top_factors) = 'array'),
  synthetic boolean NOT NULL DEFAULT false, synthetic_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (prediction_id, order_id, order_item_id),
  UNIQUE (prediction_id, order_id, product_item_id, score),
  CHECK (product_item_id = order_id || '-' || order_item_id)
);
CREATE TABLE ml.order_prediction_scores (
  prediction_id uuid NOT NULL REFERENCES ml.predictions,
  order_id text NOT NULL, score numeric(12,10) NOT NULL CHECK (score >= 0 AND score <= 1),
  aggregation_rule text NOT NULL CHECK (aggregation_rule = 'max-v1'),
  top_product_item_id text NOT NULL, top_item_score numeric(12,10) NOT NULL CHECK (top_item_score >= 0 AND top_item_score <= 1),
  item_count integer NOT NULL CHECK (item_count > 0), item_value numeric(14,2) NOT NULL CHECK (item_value >= 0),
  risk_context jsonb NOT NULL DEFAULT '{}'::jsonb, top_factors jsonb NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(top_factors) = 'array'),
  synthetic boolean NOT NULL DEFAULT false, synthetic_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY (prediction_id, order_id),
  FOREIGN KEY (prediction_id, order_id, top_product_item_id, top_item_score)
    REFERENCES ml.item_prediction_scores(prediction_id, order_id, product_item_id, score),
  CHECK (score = top_item_score)
);

CREATE FUNCTION ml.immutable_row() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION '% is immutable', TG_TABLE_NAME; END; $$;
CREATE TRIGGER model_releases_immutable BEFORE UPDATE OR DELETE ON ml.model_releases FOR EACH ROW EXECUTE FUNCTION ml.immutable_row();
CREATE TRIGGER model_thresholds_immutable BEFORE UPDATE OR DELETE ON ml.model_thresholds FOR EACH ROW EXECUTE FUNCTION ml.immutable_row();
CREATE TRIGGER item_scores_immutable BEFORE UPDATE OR DELETE ON ml.item_prediction_scores FOR EACH ROW EXECUTE FUNCTION ml.immutable_row();
CREATE TRIGGER order_scores_immutable BEFORE UPDATE OR DELETE ON ml.order_prediction_scores FOR EACH ROW EXECUTE FUNCTION ml.immutable_row();
CREATE FUNCTION ml.prediction_state_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'predictions are immutable'; END IF;
  IF TG_OP = 'INSERT' AND NEW.state = 'ACTIVE' AND (SELECT evaluation_status FROM ml.model_releases WHERE model_release_id=NEW.model_release_id) <> 'CONFIRMATORY' THEN RAISE EXCEPTION 'only confirmatory releases may be ACTIVE'; END IF;
  IF TG_OP = 'UPDATE' THEN
    IF NEW.prediction_id<>OLD.prediction_id OR NEW.model_release_id<>OLD.model_release_id OR NEW.threshold_version<>OLD.threshold_version OR NEW.source_run_id<>OLD.source_run_id OR NEW.input_hash<>OLD.input_hash OR NEW.model_input_hash<>OLD.model_input_hash OR NEW.scored_at<>OLD.scored_at OR NEW.created_at<>OLD.created_at THEN RAISE EXCEPTION 'prediction snapshot is immutable'; END IF;
    IF NOT ((OLD.state='READY' AND NEW.state IN ('ACTIVE','REJECTED')) OR (OLD.state='ACTIVE' AND NEW.state='SUPERSEDED')) THEN RAISE EXCEPTION 'invalid prediction state transition'; END IF;
    IF NEW.state='ACTIVE' AND (SELECT evaluation_status FROM ml.model_releases WHERE model_release_id=NEW.model_release_id) <> 'CONFIRMATORY' THEN RAISE EXCEPTION 'only confirmatory releases may be ACTIVE'; END IF;
  END IF;
  IF NEW.state='ACTIVE' AND NEW.activated_at IS NULL THEN NEW.activated_at := now(); END IF; RETURN NEW;
END; $$;
CREATE TRIGGER predictions_state BEFORE INSERT OR UPDATE OR DELETE ON ml.predictions FOR EACH ROW EXECUTE FUNCTION ml.prediction_state_guard();

CREATE VIEW ml.v_risk_items_for_web AS
SELECT i.prediction_id, i.order_id, i.order_item_id, i.product_item_id, i.score AS risk_score,
 CASE WHEN i.score >= t.high_from THEN 'HIGH' WHEN i.score >= t.medium_from THEN 'MEDIUM' ELSE 'LOW' END AS risk_level,
 i.top_factors, i.synthetic, i.synthetic_metadata, i.risk_context AS context,
 p.scored_at, p.model_release_id, r.release_version AS model_version, t.threshold_version
FROM ml.item_prediction_scores i JOIN ml.predictions p USING (prediction_id)
JOIN ml.model_releases r USING (model_release_id)
JOIN ml.model_thresholds t ON (t.model_release_id=p.model_release_id AND t.threshold_version=p.threshold_version) WHERE p.state='ACTIVE';
CREATE VIEW ml.v_risk_orders_for_web AS
SELECT o.prediction_id, o.order_id, o.score AS risk_score, o.top_product_item_id, o.top_item_score,
 o.item_count, o.item_value,
 CASE WHEN o.score >= t.high_from THEN 'HIGH' WHEN o.score >= t.medium_from THEN 'MEDIUM' ELSE 'LOW' END AS risk_level,
 o.top_factors, o.synthetic, o.synthetic_metadata, o.risk_context AS context,
 p.scored_at, p.model_release_id, r.release_version AS model_version, t.threshold_version
FROM ml.order_prediction_scores o JOIN ml.predictions p USING (prediction_id)
JOIN ml.model_releases r USING (model_release_id)
JOIN ml.model_thresholds t ON (t.model_release_id=p.model_release_id AND t.threshold_version=p.threshold_version) WHERE p.state='ACTIVE';

RESET ROLE;
REVOKE ALL ON ml.model_releases, ml.model_thresholds, ml.predictions, ml.item_prediction_scores, ml.order_prediction_scores FROM PUBLIC, app_runtime, reader;
GRANT SELECT ON ml.v_risk_items_for_web, ml.v_risk_orders_for_web TO app_runtime, reader;
GRANT SELECT, INSERT ON ml.model_releases, ml.model_thresholds, ml.predictions, ml.item_prediction_scores, ml.order_prediction_scores TO transform_runner;

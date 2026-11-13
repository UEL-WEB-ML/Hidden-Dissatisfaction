\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

DROP VIEW ml.v_risk_items_for_web;
DROP VIEW ml.v_risk_orders_for_web;

-- P6.2 tightens the persisted inference contract without changing V001.
ALTER TABLE ml.model_thresholds
  ALTER COLUMN medium_from TYPE numeric(18,17),
  ALTER COLUMN high_from TYPE numeric(18,17),
  ADD COLUMN selection_policy text NOT NULL DEFAULT 'validation-f1-v1';

ALTER TABLE ml.predictions
  ADD CONSTRAINT predictions_input_hash_sha256_ck
    CHECK (input_hash ~ '^[0-9a-fA-F]{64}$'),
  ADD CONSTRAINT predictions_model_input_hash_sha256_ck
    CHECK (model_input_hash ~ '^[0-9a-fA-F]{64}$');

CREATE VIEW ml.v_risk_items_for_web AS
SELECT i.prediction_id, i.order_id, i.order_item_id, i.product_item_id,
  i.score AS risk_score,
  CASE WHEN i.score >= t.high_from THEN 'HIGH'
       WHEN i.score >= t.medium_from THEN 'MEDIUM' ELSE 'LOW' END AS risk_level,
  r.aggregation_rule, i.top_factors, i.synthetic, i.synthetic_metadata,
  i.risk_context AS context, p.scored_at AS predicted_at,
  p.scored_at, p.model_release_id, r.release_version AS model_version,
  t.threshold_version
FROM ml.item_prediction_scores i
JOIN ml.predictions p USING (prediction_id)
JOIN ml.model_releases r USING (model_release_id)
JOIN ml.model_thresholds t ON (t.model_release_id=p.model_release_id
  AND t.threshold_version=p.threshold_version)
WHERE p.state='ACTIVE';

CREATE VIEW ml.v_risk_orders_for_web AS
SELECT o.prediction_id, o.order_id, o.score AS risk_score,
  o.top_product_item_id, o.top_item_score, o.item_count,
  o.item_count AS items_count, o.item_value,
  CASE WHEN o.score >= t.high_from THEN 'HIGH'
       WHEN o.score >= t.medium_from THEN 'MEDIUM' ELSE 'LOW' END AS risk_level,
  o.aggregation_rule, o.top_factors, o.synthetic, o.synthetic_metadata,
  o.risk_context AS context, p.scored_at AS predicted_at,
  p.scored_at, p.model_release_id, r.release_version AS model_version,
  t.threshold_version
FROM ml.order_prediction_scores o
JOIN ml.predictions p USING (prediction_id)
JOIN ml.model_releases r USING (model_release_id)
JOIN ml.model_thresholds t ON (t.model_release_id=p.model_release_id
  AND t.threshold_version=p.threshold_version)
WHERE p.state='ACTIVE';

RESET ROLE;
GRANT SELECT ON ml.v_risk_items_for_web, ml.v_risk_orders_for_web TO app_runtime, reader;

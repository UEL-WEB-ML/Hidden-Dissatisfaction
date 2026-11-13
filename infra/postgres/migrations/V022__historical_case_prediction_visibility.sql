\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

CREATE OR REPLACE FUNCTION app.p7_case_guard() RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, app, ml
AS $$
DECLARE
  score_row ml.order_prediction_scores%ROWTYPE;
  prediction_state text;
BEGIN
  IF TG_OP = 'INSERT' THEN
    SELECT state INTO prediction_state
    FROM ml.predictions
    WHERE prediction_id = NEW.prediction_id
    FOR SHARE;
  ELSE
    SELECT state INTO prediction_state
    FROM ml.predictions
    WHERE prediction_id = NEW.prediction_id;
  END IF;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'prediction does not exist';
  END IF;
  IF TG_OP = 'INSERT' AND prediction_state <> 'ACTIVE' THEN
    RAISE EXCEPTION 'prediction must be ACTIVE when a case is created';
  END IF;

  SELECT * INTO score_row
  FROM ml.order_prediction_scores
  WHERE prediction_id = NEW.prediction_id AND order_id = NEW.order_id;
  IF NOT FOUND OR score_row.aggregation_rule <> 'max-v1'
     OR score_row.score <> score_row.top_item_score THEN
    RAISE EXCEPTION 'order prediction snapshot mismatch';
  END IF;

  IF TG_OP = 'UPDATE' AND (
    NEW.case_id IS DISTINCT FROM OLD.case_id
    OR NEW.order_id IS DISTINCT FROM OLD.order_id
    OR NEW.prediction_id IS DISTINCT FROM OLD.prediction_id
    OR NEW.aggregation_rule IS DISTINCT FROM OLD.aggregation_rule
    OR NEW.original_queued_at IS DISTINCT FROM OLD.original_queued_at
  ) THEN
    RAISE EXCEPTION 'case snapshot is immutable';
  END IF;
  RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION app.p7_case_guard() FROM PUBLIC;

DROP VIEW ml.v_risk_items_for_web;
DROP VIEW ml.v_risk_orders_for_web;

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
WHERE p.state = 'ACTIVE'
   OR EXISTS (
     SELECT 1 FROM app.review_cases c
     WHERE c.prediction_id = i.prediction_id AND c.order_id = i.order_id
   );

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
WHERE p.state = 'ACTIVE'
   OR EXISTS (
     SELECT 1 FROM app.review_cases c
     WHERE c.prediction_id = o.prediction_id AND c.order_id = o.order_id
   );

CREATE VIEW ml.v_queue_seed_orders AS
SELECT o.prediction_id, o.order_id, o.score,
  CASE WHEN o.score >= t.high_from THEN 'HIGH'
       WHEN o.score >= t.medium_from THEN 'MEDIUM' ELSE 'LOW' END AS risk_level,
  o.aggregation_rule
FROM ml.order_prediction_scores o
JOIN ml.predictions p USING (prediction_id)
JOIN ml.model_thresholds t ON (t.model_release_id=p.model_release_id
  AND t.threshold_version=p.threshold_version)
WHERE p.state = 'ACTIVE';

REVOKE ALL ON ml.v_risk_items_for_web, ml.v_risk_orders_for_web,
  ml.v_queue_seed_orders FROM PUBLIC;
GRANT SELECT ON ml.v_risk_items_for_web, ml.v_risk_orders_for_web TO app_runtime, reader;
GRANT SELECT ON ml.v_queue_seed_orders TO app_runtime;

RESET ROLE;

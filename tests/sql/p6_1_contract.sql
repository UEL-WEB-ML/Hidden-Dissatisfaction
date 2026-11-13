\set ON_ERROR_STOP on
BEGIN;
INSERT INTO ml.model_releases VALUES ('00000000-0000-0000-0000-000000000001','test-ex','m','1','https://x',repeat('a',64),'f1',repeat('b',64),'git','snapshot','00000000-0000-0000-0000-000000000011','max-v1','EXPLORATORY_NON_CONFIRMATORY',now());
INSERT INTO ml.model_releases VALUES ('00000000-0000-0000-0000-000000000002','test-cf','m','1','https://x',repeat('a',64),'f1',repeat('b',64),'git','snapshot','00000000-0000-0000-0000-000000000012','max-v1','CONFIRMATORY',now());
INSERT INTO ml.model_thresholds(model_release_id,threshold_version,medium_from,high_from) VALUES ('00000000-0000-0000-0000-000000000001','1',.5,.8),('00000000-0000-0000-0000-000000000002','1',.5,.8);

DO $$ BEGIN
  BEGIN INSERT INTO ml.model_thresholds VALUES ('00000000-0000-0000-0000-000000000002','bad',.8,.5,now()); RAISE EXCEPTION 'ordering accepted'; EXCEPTION WHEN check_violation THEN NULL; END;
  BEGIN UPDATE ml.model_releases SET model_name='x' WHERE model_release_id='00000000-0000-0000-0000-000000000002'; RAISE EXCEPTION 'immutable release accepted'; EXCEPTION WHEN raise_exception THEN NULL; END;
  BEGIN INSERT INTO ml.predictions VALUES ('10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001','1','20000000-0000-0000-0000-000000000001','i','m',now(),'ACTIVE',now(),NULL); RAISE EXCEPTION 'exploratory activation accepted'; EXCEPTION WHEN raise_exception THEN NULL; END;
END $$;
INSERT INTO ml.predictions(prediction_id,model_release_id,threshold_version,source_run_id,input_hash,model_input_hash,scored_at,state) VALUES ('10000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002','1','20000000-0000-0000-0000-000000000002','i','m',now(),'READY');
UPDATE ml.predictions SET state='ACTIVE' WHERE prediction_id='10000000-0000-0000-0000-000000000002';
INSERT INTO ml.item_prediction_scores VALUES ('10000000-0000-0000-0000-000000000002','o','1','o-1',.5,'{}','[]',false,'{}'),('10000000-0000-0000-0000-000000000002','o','2','o-2',.8,'{}','[]',false,'{}');
INSERT INTO ml.order_prediction_scores VALUES ('10000000-0000-0000-0000-000000000002','o',.8,'max-v1','o-2',.8,2,1,'{}','[]',false,'{}');
DO $$ BEGIN
  BEGIN INSERT INTO ml.predictions VALUES ('10000000-0000-0000-0000-000000000003','00000000-0000-0000-0000-000000000002','1','20000000-0000-0000-0000-000000000003','i','m',now(),'ACTIVE',now(),NULL); RAISE EXCEPTION 'two active rows accepted'; EXCEPTION WHEN unique_violation THEN NULL; END;
  IF (SELECT risk_level FROM ml.v_risk_items_for_web WHERE risk_score=.5) <> 'MEDIUM' OR (SELECT risk_level FROM ml.v_risk_items_for_web WHERE risk_score=.8) <> 'HIGH' THEN RAISE EXCEPTION 'risk boundary failure'; END IF;
  IF NOT EXISTS (SELECT 1 FROM ml.v_risk_orders_for_web WHERE model_version='test-cf' AND threshold_version='1' AND scored_at IS NOT NULL) THEN RAISE EXCEPTION 'view metadata missing'; END IF;
END $$;
ROLLBACK;

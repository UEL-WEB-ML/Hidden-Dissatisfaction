\set ON_ERROR_STOP on
BEGIN;
DO $$ BEGIN
 IF (SELECT value FROM app.parameters WHERE param_key='max_contact') <> '3' THEN RAISE EXCEPTION 'seed parameters missing'; END IF;
 IF NOT EXISTS (SELECT 1 FROM app.parameter_definitions WHERE param_key='capacity') THEN RAISE EXCEPTION 'definitions missing'; END IF;
 IF (SELECT count(*) FROM app.audit_events WHERE provenance='QUEUE_SEED') <> 0 THEN RAISE EXCEPTION 'unexpected seed audit'; END IF;
END $$;
DO $$ BEGIN
 BEGIN UPDATE app.parameters SET value='9' WHERE param_key='capacity'; RAISE EXCEPTION 'parameter mutation accepted'; EXCEPTION WHEN raise_exception THEN NULL; END;
 BEGIN DELETE FROM app.audit_events; RAISE EXCEPTION 'audit mutation accepted'; EXCEPTION WHEN raise_exception THEN NULL; END;
END $$;
ROLLBACK;

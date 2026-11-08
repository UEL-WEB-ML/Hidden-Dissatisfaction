\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;
DROP INDEX IF EXISTS app.parameter_bundles_revision_idx;
ALTER TABLE app.review_cycles ADD COLUMN parameter_bundle_id uuid REFERENCES app.parameter_bundles(bundle_id);
CREATE UNIQUE INDEX review_cycles_one_open_per_case ON app.review_cycles(case_id) WHERE ended_at IS NULL;
DROP TRIGGER IF EXISTS review_cycles_immutable ON app.review_cycles;
CREATE FUNCTION app.p9_review_cycle_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF OLD.ended_at IS NOT NULL OR NEW.ended_at IS NULL OR NEW.cycle_id<>OLD.cycle_id OR NEW.case_id<>OLD.case_id OR NEW.cycle_no<>OLD.cycle_no OR NEW.started_at<>OLD.started_at OR NEW.sla_due_at<>OLD.sla_due_at OR NEW.parameter_version IS DISTINCT FROM OLD.parameter_version OR NEW.parameter_bundle_id IS DISTINCT FROM OLD.parameter_bundle_id OR NEW.reopen_reason IS DISTINCT FROM OLD.reopen_reason OR NEW.reopened_by IS DISTINCT FROM OLD.reopened_by THEN RAISE EXCEPTION 'review cycle permits only controlled closure'; END IF; RETURN NEW; END $$;
CREATE TRIGGER review_cycles_close_guard BEFORE UPDATE ON app.review_cycles FOR EACH ROW EXECUTE FUNCTION app.p9_review_cycle_guard();
CREATE FUNCTION app.close_review_cycle(p_cycle_id uuid, p_ended_at timestamptz DEFAULT now()) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=app,public AS $$ BEGIN UPDATE review_cycles SET ended_at=p_ended_at WHERE cycle_id=p_cycle_id AND ended_at IS NULL; IF NOT FOUND THEN RAISE EXCEPTION 'cycle is missing or already closed'; END IF; END $$;
REVOKE ALL ON FUNCTION app.close_review_cycle(uuid,timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.close_review_cycle(uuid,timestamptz) TO app_runtime;
RESET ROLE;

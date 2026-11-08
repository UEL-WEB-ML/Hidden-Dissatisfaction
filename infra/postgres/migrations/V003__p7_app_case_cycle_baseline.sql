\set ON_ERROR_STOP on
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
SET ROLE hidden_dissatisfaction_owner;

CREATE TABLE app.users (
 user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), username varchar(50) NOT NULL UNIQUE,
 password_hash text NOT NULL, full_name varchar(100) NOT NULL,
 role varchar(20) NOT NULL CHECK (role IN ('SPECIALIST','MANAGER')),
 preferred_language varchar(2) CHECK (preferred_language IN ('vi','en')), is_active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE app.review_cases (
 case_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), order_id varchar(32) NOT NULL UNIQUE,
 prediction_id uuid NOT NULL REFERENCES ml.predictions(prediction_id), aggregation_rule varchar(20) NOT NULL CHECK (aggregation_rule='max-v1'),
 status varchar(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','IN_PROGRESS','COMPLETED','SKIPPED')),
 assignee_id uuid REFERENCES app.users, cycle_no smallint NOT NULL DEFAULT 1 CHECK (cycle_no >= 1),
 original_queued_at timestamptz NOT NULL DEFAULT now(), outcome varchar(30) CHECK (outcome IN ('HAS_ISSUE','NO_ISSUE','DUPLICATE')),
 skip_reason varchar(30) CHECK (skip_reason IN ('UNREACHABLE','DUPLICATE','REFUSED','NOT_APPLICABLE','OTHER')),
 close_note text, closed_at timestamptz, reopen_count smallint NOT NULL DEFAULT 0 CHECK (reopen_count >= 0),
 updated_at timestamptz NOT NULL DEFAULT now(), row_version integer NOT NULL DEFAULT 0
);
CREATE TABLE app.review_cycles (
 cycle_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), case_id uuid NOT NULL REFERENCES app.review_cases(case_id), cycle_no smallint NOT NULL CHECK(cycle_no >= 1),
 started_at timestamptz NOT NULL, ended_at timestamptz, reopen_reason text, reopened_by uuid REFERENCES app.users(user_id),
 sla_due_at timestamptz NOT NULL, parameter_version varchar(30), UNIQUE(case_id,cycle_no)
);
CREATE FUNCTION app.p7_case_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE s ml.order_prediction_scores%ROWTYPE; p ml.predictions%ROWTYPE;
BEGIN
 SELECT * INTO p FROM ml.predictions WHERE prediction_id=NEW.prediction_id AND state='ACTIVE';
 IF NOT FOUND THEN RAISE EXCEPTION 'prediction must be ACTIVE'; END IF;
 SELECT * INTO s FROM ml.order_prediction_scores WHERE prediction_id=NEW.prediction_id AND order_id=NEW.order_id;
 IF NOT FOUND OR s.aggregation_rule <> 'max-v1' OR s.score <> s.top_item_score THEN RAISE EXCEPTION 'order prediction snapshot mismatch'; END IF;
 IF TG_OP='UPDATE' AND (NEW.case_id<>OLD.case_id OR NEW.order_id<>OLD.order_id OR NEW.prediction_id<>OLD.prediction_id OR NEW.aggregation_rule<>OLD.aggregation_rule OR NEW.original_queued_at<>OLD.original_queued_at) THEN RAISE EXCEPTION 'case snapshot is immutable'; END IF;
 RETURN NEW; END $$;
CREATE TRIGGER review_cases_guard BEFORE INSERT OR UPDATE ON app.review_cases FOR EACH ROW EXECUTE FUNCTION app.p7_case_guard();
CREATE FUNCTION app.p7_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION '% is append-only',TG_TABLE_NAME; END $$;
CREATE TRIGGER review_cycles_immutable BEFORE UPDATE OR DELETE ON app.review_cycles FOR EACH ROW EXECUTE FUNCTION app.p7_immutable();
RESET ROLE;

\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- Keep the original P7 records immutable while adding the fields required by
-- API Contract 0.5. New P9 writes must always populate the cycle reference.
ALTER TABLE app.contact_attempts ADD COLUMN cycle_id uuid REFERENCES app.review_cycles(cycle_id);
ALTER TABLE app.contact_attempts ADD COLUMN contact_result varchar(20)
  CHECK (contact_result IN ('REACHED', 'NO_ANSWER', 'CALLBACK', 'WRONG_NUMBER'));
ALTER TABLE app.contact_attempts ADD COLUMN note text;
ALTER TABLE app.contact_attempts ADD COLUMN next_contact_date date;
ALTER TABLE app.contact_attempts ADD COLUMN evidence_ref text;
CREATE INDEX contact_attempts_cycle_idx ON app.contact_attempts(cycle_id, attempt_no);

ALTER TABLE app.manager_decisions ADD COLUMN cycle_id uuid REFERENCES app.review_cycles(cycle_id);
ALTER TABLE app.manager_decisions ADD COLUMN next_step text;
ALTER TABLE app.manager_decisions ADD COLUMN next_step_assignee_id uuid REFERENCES app.users(user_id);
ALTER TABLE app.manager_decisions ADD COLUMN due_date date;
ALTER TABLE app.manager_decisions ADD COLUMN note text;

-- Runtime writes are constrained by the application transaction and existing
-- database guards/triggers. Append-only workflow tables retain no UPDATE/DELETE
-- grant, except controlled case/cycle/assignment lifecycle fields.
GRANT INSERT, UPDATE ON app.review_cases, app.review_cycles TO app_runtime;
GRANT INSERT, UPDATE (released_at, release_reason) ON app.assignments TO app_runtime;
GRANT INSERT ON app.contact_attempts, app.contact_evidence, app.case_comments, app.manager_decisions TO app_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO app_runtime;

RESET ROLE;

\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

CREATE TABLE app.assignments (
 assignment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), case_id uuid NOT NULL REFERENCES app.review_cases(case_id),
 assignee_id uuid NOT NULL REFERENCES app.users(user_id), assigned_at timestamptz NOT NULL DEFAULT now(),
 released_at timestamptz, release_reason text, CHECK (released_at IS NULL OR released_at >= assigned_at)
);
CREATE UNIQUE INDEX assignments_one_active_per_case ON app.assignments(case_id) WHERE released_at IS NULL;
CREATE INDEX assignments_assignee_active_idx ON app.assignments(assignee_id) WHERE released_at IS NULL;

CREATE TABLE app.contact_attempts (
 attempt_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), case_id uuid NOT NULL REFERENCES app.review_cases(case_id),
 assignment_id uuid REFERENCES app.assignments(assignment_id), attempt_no smallint NOT NULL CHECK (attempt_no > 0),
 channel varchar(20) NOT NULL CHECK (channel IN ('PHONE','EMAIL','CHAT','OTHER')), status varchar(20) NOT NULL CHECK (status IN ('PLANNED','STARTED','COMPLETED','FAILED')),
 attempted_at timestamptz, outcome text, created_by uuid NOT NULL REFERENCES app.users(user_id), created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(case_id, attempt_no)
);
CREATE INDEX contact_attempts_case_idx ON app.contact_attempts(case_id, created_at);

CREATE TABLE app.contact_evidence (
 evidence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), case_id uuid NOT NULL REFERENCES app.review_cases(case_id), attempt_id uuid REFERENCES app.contact_attempts(attempt_id),
 storage_key text, content_type varchar(100), metadata jsonb NOT NULL DEFAULT '{}'::jsonb, attached_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL DEFAULT (now() + interval '24 hours'), attached_by uuid REFERENCES app.users(user_id),
 CHECK (expires_at >= attached_at), CHECK (storage_key IS NOT NULL OR metadata <> '{}'::jsonb)
);
CREATE INDEX contact_evidence_ttl_idx ON app.contact_evidence(expires_at);
CREATE INDEX contact_evidence_case_idx ON app.contact_evidence(case_id);

CREATE TABLE app.case_comments (
 comment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), case_id uuid NOT NULL REFERENCES app.review_cases(case_id), author_id uuid NOT NULL REFERENCES app.users(user_id),
 body text NOT NULL CHECK (length(trim(body)) > 0), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX case_comments_case_idx ON app.case_comments(case_id, created_at);

CREATE TABLE app.manager_decisions (
 decision_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), case_id uuid NOT NULL REFERENCES app.review_cases(case_id), decided_by uuid NOT NULL REFERENCES app.users(user_id),
 decision varchar(30) NOT NULL CHECK (decision IN ('NO_FURTHER_ACTION','FOLLOW_UP_CUSTOMER','WORK_WITH_SELLER','REFER_AFTER_SALES')),
 rationale text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX manager_decisions_case_idx ON app.manager_decisions(case_id, created_at);

CREATE FUNCTION app.p7_workflow_append_only() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION '% is append-only', TG_TABLE_NAME; END $$;
CREATE TRIGGER contact_attempts_immutable BEFORE UPDATE OR DELETE ON app.contact_attempts FOR EACH ROW EXECUTE FUNCTION app.p7_workflow_append_only();
CREATE TRIGGER contact_evidence_immutable BEFORE UPDATE OR DELETE ON app.contact_evidence FOR EACH ROW EXECUTE FUNCTION app.p7_workflow_append_only();
CREATE TRIGGER case_comments_immutable BEFORE UPDATE OR DELETE ON app.case_comments FOR EACH ROW EXECUTE FUNCTION app.p7_workflow_append_only();
CREATE TRIGGER manager_decisions_immutable BEFORE UPDATE OR DELETE ON app.manager_decisions FOR EACH ROW EXECUTE FUNCTION app.p7_workflow_append_only();
RESET ROLE;

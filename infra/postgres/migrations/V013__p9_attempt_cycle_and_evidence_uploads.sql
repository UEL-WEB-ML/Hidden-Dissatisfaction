\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- Attempt numbers restart in every review cycle (BRD 6.8), so uniqueness moves
-- from the case to the cycle. P9 writes always populate cycle_id.
ALTER TABLE app.contact_attempts DROP CONSTRAINT contact_attempts_case_id_attempt_no_key;
CREATE UNIQUE INDEX contact_attempts_cycle_attempt_no_key
  ON app.contact_attempts(cycle_id, attempt_no) WHERE cycle_id IS NOT NULL;

-- contact_evidence is append-only, so uploads wait here until a contact claims
-- them; attaching copies the file into contact_evidence in the same transaction.
CREATE TABLE app.evidence_uploads (
 upload_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 uploaded_by uuid NOT NULL REFERENCES app.users(user_id),
 storage_key text NOT NULL UNIQUE,
 file_name varchar(100) NOT NULL,
 content_type varchar(100) NOT NULL CHECK (content_type IN ('image/png', 'image/jpeg', 'application/pdf')),
 file_size integer NOT NULL CHECK (file_size BETWEEN 1 AND 5242880),
 uploaded_at timestamptz NOT NULL DEFAULT now(),
 attached_at timestamptz
);
CREATE INDEX evidence_uploads_unattached_idx ON app.evidence_uploads(uploaded_at) WHERE attached_at IS NULL;
CREATE FUNCTION app.p9_upload_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF TG_OP = 'DELETE' OR OLD.attached_at IS NOT NULL THEN RAISE EXCEPTION 'evidence upload is already attached'; END IF;
 RETURN NEW; END $$;
CREATE TRIGGER evidence_uploads_guard BEFORE UPDATE OR DELETE ON app.evidence_uploads FOR EACH ROW EXECUTE FUNCTION app.p9_upload_guard();
GRANT SELECT, INSERT ON app.evidence_uploads TO app_runtime;
GRANT UPDATE (attached_at) ON app.evidence_uploads TO app_runtime;
GRANT SELECT ON app.evidence_uploads TO reader;

RESET ROLE;

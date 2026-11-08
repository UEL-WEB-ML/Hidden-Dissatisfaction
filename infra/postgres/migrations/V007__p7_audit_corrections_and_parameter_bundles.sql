\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;
ALTER TABLE app.audit_events ADD COLUMN actor_kind varchar(10) NOT NULL DEFAULT 'USER' CHECK (actor_kind IN ('USER','SYSTEM'));
ALTER TABLE app.audit_events ADD CONSTRAINT audit_actor_kind_fk CHECK ((actor_kind='USER' AND actor_id IS NOT NULL) OR (actor_kind='SYSTEM' AND actor_id IS NULL));
ALTER TABLE app.audit_events ADD CONSTRAINT audit_queue_seed_kind_ck CHECK (provenance <> 'QUEUE_SEED' OR (actor_kind='SYSTEM' AND event_type='QUEUE_SEED'));
CREATE INDEX audit_events_case_created_idx ON app.audit_events(case_id, created_at);
CREATE INDEX audit_events_type_idx ON app.audit_events(event_type, created_at);

CREATE TABLE app.audit_corrections (
 correction_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, event_id bigint NOT NULL REFERENCES app.audit_events(event_id),
 corrected_by uuid NOT NULL REFERENCES app.users(user_id), correction text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE FUNCTION app.p7_correction_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'audit_corrections is append-only'; END $$;
CREATE TRIGGER audit_corrections_immutable BEFORE UPDATE OR DELETE ON app.audit_corrections FOR EACH ROW EXECUTE FUNCTION app.p7_correction_immutable();

CREATE TABLE app.parameter_bundles (
 bundle_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), revision integer NOT NULL CHECK (revision > 0),
 parameter_id bigint NOT NULL REFERENCES app.parameters(parameter_id), created_by uuid REFERENCES app.users(user_id), created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(revision, parameter_id)
);
CREATE UNIQUE INDEX parameter_bundles_revision_idx ON app.parameter_bundles(revision);
CREATE FUNCTION app.p7_bundle_immutable() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'parameter_bundles is append-only'; END $$;
CREATE TRIGGER parameter_bundles_immutable BEFORE UPDATE OR DELETE ON app.parameter_bundles FOR EACH ROW EXECUTE FUNCTION app.p7_bundle_immutable();
RESET ROLE;

\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- The V013 guard already rejects DELETE of attached uploads. Granting DELETE lets
-- the retention job purge expired *unattached* rows only; the trigger still
-- protects every attached row, so attached evidence cannot be removed.
GRANT DELETE ON app.evidence_uploads TO app_runtime;
CREATE OR REPLACE FUNCTION app.p9_upload_guard() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
 IF OLD.attached_at IS NOT NULL THEN RAISE EXCEPTION 'attached evidence is retained'; END IF;
 IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
 RETURN NEW; END $$;

RESET ROLE;

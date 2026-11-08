\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- The snapshot guard reads ml.predictions/order scores, which app_runtime must
-- not touch directly (V001). Run it with the owner's rights and a pinned
-- search_path so runtime claim/assign/close updates can pass the guard.
ALTER FUNCTION app.p7_case_guard() SECURITY DEFINER;
ALTER FUNCTION app.p7_case_guard() SET search_path = pg_catalog, app, ml;

RESET ROLE;

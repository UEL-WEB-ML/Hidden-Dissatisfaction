\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;
GRANT INSERT ON app.parameters, app.parameter_bundles, app.audit_events TO app_runtime;
GRANT USAGE ON SEQUENCE app.parameters_parameter_id_seq, app.audit_events_event_id_seq TO app_runtime;
RESET ROLE;

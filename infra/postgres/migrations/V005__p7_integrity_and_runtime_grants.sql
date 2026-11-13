\set ON_ERROR_STOP on
REVOKE ALL ON app.review_cases, app.review_cycles, app.users, app.parameters, app.parameter_definitions, app.audit_events FROM PUBLIC, app_runtime, reader;
GRANT SELECT ON app.review_cases, app.review_cycles, app.users, app.parameters, app.parameter_definitions, app.audit_events TO app_runtime, reader;
GRANT INSERT ON app.audit_events TO app_runtime;
GRANT INSERT ON app.review_cases, app.review_cycles TO app_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO app_runtime;

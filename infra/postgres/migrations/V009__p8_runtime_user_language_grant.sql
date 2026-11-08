\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;
GRANT UPDATE (preferred_language) ON app.users TO app_runtime;
RESET ROLE;

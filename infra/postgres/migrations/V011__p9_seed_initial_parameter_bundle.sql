\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;
INSERT INTO app.parameter_bundles(revision, parameter_id)
SELECT 1, parameter_id
FROM app.parameters
WHERE NOT EXISTS (SELECT 1 FROM app.parameter_bundles);
RESET ROLE;

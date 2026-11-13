\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- /config must show ML thresholds without granting app_runtime raw ml.* tables.
CREATE VIEW ml.v_active_thresholds AS
SELECT t.threshold_version, t.medium_from, t.high_from, r.release_version AS model_version
FROM ml.predictions p
JOIN ml.model_releases r ON r.model_release_id = p.model_release_id
JOIN ml.model_thresholds t
  ON t.model_release_id = p.model_release_id AND t.threshold_version = p.threshold_version
WHERE p.state = 'ACTIVE';
GRANT SELECT ON ml.v_active_thresholds TO app_runtime, reader;

RESET ROLE;

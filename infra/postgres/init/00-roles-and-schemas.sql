\set ON_ERROR_STOP on

CREATE ROLE hidden_dissatisfaction_owner NOLOGIN;
CREATE ROLE migrator NOLOGIN NOINHERIT IN ROLE hidden_dissatisfaction_owner;
CREATE ROLE ingest_writer NOLOGIN;
CREATE ROLE transform_runner NOLOGIN;
CREATE ROLE app_runtime NOLOGIN;
CREATE ROLE reader NOLOGIN;

DO $$
BEGIN
  EXECUTE format('REVOKE ALL ON DATABASE %I FROM PUBLIC', current_database());
END
$$;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

CREATE SCHEMA app AUTHORIZATION hidden_dissatisfaction_owner;
CREATE SCHEMA bronze AUTHORIZATION hidden_dissatisfaction_owner;
CREATE SCHEMA silver AUTHORIZATION hidden_dissatisfaction_owner;
CREATE SCHEMA gold AUTHORIZATION hidden_dissatisfaction_owner;
CREATE SCHEMA ml AUTHORIZATION hidden_dissatisfaction_owner;

DO $$
BEGIN
  EXECUTE format('GRANT CONNECT ON DATABASE %I TO migrator, ingest_writer, transform_runner, app_runtime, reader', current_database());
END
$$;
GRANT USAGE ON SCHEMA app TO app_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA app TO app_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO app_runtime;
GRANT USAGE ON SCHEMA gold, ml TO app_runtime, reader;
GRANT SELECT ON ALL TABLES IN SCHEMA gold, ml TO app_runtime, reader;

GRANT USAGE, CREATE ON SCHEMA bronze TO ingest_writer;
GRANT USAGE ON SCHEMA bronze TO transform_runner;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bronze TO ingest_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO transform_runner;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA bronze TO ingest_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bronze TO transform_runner;
GRANT USAGE, CREATE ON SCHEMA silver, gold, ml TO transform_runner;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA silver, gold, ml TO transform_runner;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA silver, gold, ml TO transform_runner;

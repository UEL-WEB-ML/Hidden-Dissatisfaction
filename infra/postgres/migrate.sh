#!/usr/bin/env bash
# Forward-only psql migration runner. The migrations intentionally contain psql
# directives (for example \set), so Flyway cannot execute them unchanged.
set -euo pipefail

: "${POSTGRES_HOST:=postgres}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"

export PGPASSWORD
PSQL=(psql --host "$POSTGRES_HOST" --port "$POSTGRES_PORT" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1)

"${PSQL[@]}" --command '
  CREATE TABLE IF NOT EXISTS app.schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
  )
'

while IFS= read -r migration; do
  version="$(basename "$migration")"
  applied="$("${PSQL[@]}" --tuples-only --no-align --command "SELECT 1 FROM app.schema_migrations WHERE version = '$version'")"
  if [[ "$applied" == "1" ]]; then
    continue
  fi
  echo "Applying $version"
  "${PSQL[@]}" --file "$migration"
  "${PSQL[@]}" --command "INSERT INTO app.schema_migrations (version) VALUES ('$version')"
done < <(find /migrations -maxdepth 1 -type f -name 'V*__*.sql' -print | sort)

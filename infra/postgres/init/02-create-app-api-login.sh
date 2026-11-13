#!/usr/bin/env bash
set -euo pipefail

: "${HD_APP_RUNTIME_PASSWORD:?HD_APP_RUNTIME_PASSWORD must be set}"

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set ON_ERROR_STOP=1 \
  --set app_runtime_password="$HD_APP_RUNTIME_PASSWORD" <<'SQL'
CREATE ROLE app_api LOGIN PASSWORD :'app_runtime_password' IN ROLE app_runtime;
SQL

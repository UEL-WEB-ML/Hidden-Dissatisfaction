#!/usr/bin/env bash
set -euo pipefail
base="${API_BASE_URL:-http://127.0.0.1:8000}"
frontend="${FRONTEND_BASE_URL:-http://127.0.0.1:4200}"

for _ in {1..30}; do
  if curl --fail --silent "$base/health/ready" >/dev/null \
    && curl --fail --silent "$frontend/" >/dev/null; then
    break
  fi
  sleep 1
done

curl --fail --silent "$base/health/live" >/dev/null
curl --fail --silent "$base/health/ready" >/dev/null
curl --fail --silent "$frontend/" | grep -Eq '<hd-root|<app-root|<base href=' || {
  echo "frontend probe failed: expected Angular shell" >&2
  exit 1
}
echo "API and frontend smoke checks passed"

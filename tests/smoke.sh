#!/usr/bin/env bash
set -euo pipefail
base="${API_BASE_URL:-http://127.0.0.1:8000}"
frontend="${FRONTEND_BASE_URL:-http://127.0.0.1:4200}"

for _ in {1..30}; do
  if curl --fail --silent "$base/health/ready" >/dev/null \
    && curl --fail --silent "$frontend/html/login.html" >/dev/null; then
    break
  fi
  sleep 1
done

curl --fail --silent "$base/health/live" >/dev/null
curl --fail --silent "$base/health/ready" >/dev/null
test "$(curl --silent --output /dev/null --write-out '%{http_code}' "$frontend/")" = 302
curl --fail --silent "$frontend/html/login.html" | grep -Eq 'Hidden Dissatisfaction|Welcome back|Sign in' || {
  echo "frontend probe failed: expected Prototype login page" >&2
  exit 1
}
curl --fail --silent "$frontend/html/overview.html" | grep -q '<!DOCTYPE html>'
test "$(curl --silent --output /dev/null --write-out '%{http_code}' "$frontend/api/v1/auth/me")" = 401
echo "API, static Prototype, and same-origin proxy smoke checks passed"

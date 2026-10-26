#!/usr/bin/env bash
# Optional authenticated P12 walkthrough. Unavailable credentials are reported,
# not replaced with guessed credentials and not treated as production evidence.
set -euo pipefail
base="${API_BASE_URL:-http://127.0.0.1:8000}"
curl --fail --silent "$base/health/live" >/dev/null
curl --fail --silent "$base/health/ready" >/dev/null

if [[ -z "${DEMO_USERNAME:-}" || -z "${DEMO_PASSWORD:-}" ]]; then
  echo "P12 authenticated walkthrough skipped: DEMO_USERNAME/DEMO_PASSWORD unset"
  exit 0
fi
login="$(curl --fail --silent -H 'Content-Type: application/json' \
  -d "{\"username\":\"$DEMO_USERNAME\",\"password\":\"$DEMO_PASSWORD\"}" \
  "$base/api/v1/auth/login")"
token="$(python -c 'import json,sys; print(json.load(sys.stdin)["token"])' <<<"$login")"
auth=(-H "Authorization: Bearer $token")
for path in /api/v1/orders /api/v1/orders/summary /api/v1/orders/filter-options /api/v1/config /api/v1/users /api/v1/parameters; do
  curl --fail --silent "${auth[@]}" "$base$path" >/dev/null
  echo "checked $path"
done
echo "P12 authenticated API walkthrough passed"

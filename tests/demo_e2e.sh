#!/usr/bin/env bash
# Optional authenticated P12 walkthrough. Unavailable credentials are reported,
# not replaced with guessed credentials and not treated as production evidence.
set -euo pipefail
api_base="${API_BASE_URL:-http://127.0.0.1:8000}"
frontend_base="${FRONTEND_BASE_URL:-http://127.0.0.1:4200}"
curl --fail --silent "$api_base/health/live" >/dev/null
curl --fail --silent "$api_base/health/ready" >/dev/null

if [[ -z "${DEMO_USERNAME:-}" && -z "${DEMO_PASSWORD:-}" && -f data/evidence/P12-DEMO-CREDENTIALS.env ]]; then
  # shellcheck disable=SC1091
  source data/evidence/P12-DEMO-CREDENTIALS.env
fi

if [[ -z "${DEMO_USERNAME:-}" || -z "${DEMO_PASSWORD:-}" ]]; then
  echo "P12 authenticated walkthrough skipped: DEMO_USERNAME/DEMO_PASSWORD unset"
  exit 0
fi
login="$(curl --fail --silent -H 'Content-Type: application/json' \
  -d "{\"username\":\"$DEMO_USERNAME\",\"password\":\"$DEMO_PASSWORD\"}" \
  "$frontend_base/api/v1/auth/login")"
token="$(uv run --frozen python -c 'import json,sys; print(json.load(sys.stdin)["token"])' <<<"$login")"
auth=(-H "Authorization: Bearer $token")
for path in /api/v1/orders /api/v1/orders/summary /api/v1/orders/filter-options /api/v1/users; do
  curl --fail --silent "${auth[@]}" "$frontend_base$path" >/dev/null
  echo "checked $path"
done

if [[ -z "${DEMO_MANAGER_USERNAME:-}" || -z "${DEMO_MANAGER_PASSWORD:-}" ]]; then
  echo "P12 Manager walkthrough skipped: DEMO_MANAGER_USERNAME/DEMO_MANAGER_PASSWORD unset"
  exit 0
fi

manager_login="$(curl --fail --silent -H 'Content-Type: application/json' \
  -d "{\"username\":\"$DEMO_MANAGER_USERNAME\",\"password\":\"$DEMO_MANAGER_PASSWORD\"}" \
  "$frontend_base/api/v1/auth/login")"
manager_token="$(uv run --frozen python -c 'import json,sys; print(json.load(sys.stdin)["token"])' <<<"$manager_login")"
manager_auth=(-H "Authorization: Bearer $manager_token")
for path in /api/v1/config /api/v1/parameters /api/v1/dashboard /api/v1/audit-events; do
  curl --fail --silent "${manager_auth[@]}" "$frontend_base$path" >/dev/null
  echo "checked manager $path"
done

echo "P12 authenticated Specialist and Manager walkthrough passed"

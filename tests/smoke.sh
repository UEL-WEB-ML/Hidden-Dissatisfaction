#!/usr/bin/env bash
set -euo pipefail
base="${API_BASE_URL:-http://127.0.0.1:8000}"
curl --fail --silent "$base/health/live" >/dev/null
curl --fail --silent "$base/health/ready" >/dev/null
echo "API smoke checks passed"

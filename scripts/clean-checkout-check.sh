#!/usr/bin/env bash
set -euo pipefail
root="$(git rev-parse --show-toplevel)"; tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
git archive --format=tar HEAD | tar -xf - -C "$tmp"; cd "$tmp"
RELEASE_ROOT="$tmp" ./scripts/release-check.sh
set -a; . ./.env.example; set +a
docker compose config >/dev/null
echo 'clean-checkout validation passed; runtime gates remain environment-dependent'

#!/usr/bin/env bash
set -euo pipefail
root="$(git rev-parse --show-toplevel)"; cd "$root"; fail=0
grep -q 'ML grain.*product item' README.md || fail=1
grep -q 'Initial order aggregation.*max-v1' README.md || fail=1
grep -q 'does not load the full Olist dataset' README.md || fail=1
grep -q 'service_completed_successfully' compose.yaml || fail=1
tracked="$(git ls-files -co --exclude-standard)"
if printf '%s\n' "$tracked" | grep -Eiq '(^|/)(\.env$|.*\.pem$|.*\.key$|.*credentials.*|data/raw/olist/|.*\.csv$)'; then fail=1; fi
for file in RELEASE_NOTES.md docs/release/P12-gate-3-release-candidate.md scripts/demo-seed.sh tests/demo_e2e.sh; do test -f "$file" || fail=1; done
(( fail == 0 )) || { echo 'release checks failed' >&2; exit 1; }
echo 'release checks passed'

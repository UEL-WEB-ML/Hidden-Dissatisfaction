#!/usr/bin/env bash
set -euo pipefail
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  root="$(git rev-parse --show-toplevel)"
  tracked="$(git ls-files -co --exclude-standard)"
else
  root="${RELEASE_ROOT:-$(pwd)}"
  tracked="$(command find "$root" -type f -printf '%P\n')"
fi
cd "$root"; fail=0
grep -q 'ML grain.*product item' README.md || fail=1
grep -q 'Initial order aggregation.*max-v1' README.md || fail=1
grep -q 'does not load the full Olist dataset' README.md || fail=1
grep -q 'service_completed_successfully' compose.yaml || fail=1
if printf '%s\n' "$tracked" | grep -Eiq '(^|/)(\.env$|.*\.pem$|.*\.key$|.*credentials.*|data/raw/olist/|.*\.csv$)'; then fail=1; fi
for file in RELEASE_NOTES.md docs/release/P12-gate-3-release-candidate.md scripts/demo-seed.sh tests/demo_e2e.sh; do test -f "$file" || fail=1; done
(( fail == 0 )) || { echo 'release checks failed' >&2; exit 1; }
echo 'release checks passed'

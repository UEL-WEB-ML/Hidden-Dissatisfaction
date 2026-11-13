#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
prototype="$root/frontend/prototype"
test -f "$prototype/Dockerfile"; test -f "$prototype/nginx.conf"
test -f "$prototype/html/login.html"; test -f "$prototype/css/style.css"; test -f "$prototype/js/api.js"
grep -q 'return 302 /html/login.html' "$prototype/nginx.conf"
grep -q 'proxy_pass http://api:8000;' "$prototype/nginx.conf"
grep -q 'Welcome back' "$prototype/html/login.html"
! grep -R -E 'hd-root|app-root|angular' "$prototype" --include='*.html' --include='*.js'
echo "static Prototype checks passed"

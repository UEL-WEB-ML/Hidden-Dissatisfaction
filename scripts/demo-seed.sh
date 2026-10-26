#!/usr/bin/env bash
# P12 demo fixture contract. This intentionally creates no Olist rows and never
# downloads data; it only provides deterministic credentials/metadata for a demo.
set -euo pipefail
mkdir -p "${DEMO_EVIDENCE_DIR:-data/evidence}"
cat > "${DEMO_EVIDENCE_DIR:-data/evidence}/P12-SYNTHETIC.txt" <<'EOF'
SYNTHETIC DEMO ONLY
This marker belongs to the P12 fixture workflow and is not Olist data.
No production or confirmatory ML performance is represented.
EOF
echo "Synthetic demo marker written (no full-data ingestion)."

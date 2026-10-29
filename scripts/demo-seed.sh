#!/usr/bin/env bash
# P12 demo fixture contract. This intentionally creates no Olist rows and never
# downloads data. When local DEMO_* credentials are supplied, it creates or
# refreshes one synthetic Specialist account for the authenticated walkthrough.
set -euo pipefail

evidence_dir="${DEMO_EVIDENCE_DIR:-data/evidence}"
credentials_file="$evidence_dir/P12-DEMO-CREDENTIALS.env"
mkdir -p "$evidence_dir"

if [[ -z "${DEMO_USERNAME:-}" && -z "${DEMO_PASSWORD:-}" ]]; then
  if [[ -f "$credentials_file" ]]; then
    # shellcheck disable=SC1090
    source "$credentials_file"
  else
    DEMO_USERNAME="demo_specialist"
    DEMO_PASSWORD="$(openssl rand -base64 24 | tr -d '\n')"
    (
      umask 077
      printf 'DEMO_USERNAME=%q\nDEMO_PASSWORD=%q\n' "$DEMO_USERNAME" "$DEMO_PASSWORD" > "$credentials_file"
    )
    echo "Synthetic demo credentials generated in $credentials_file (Git ignored)."
  fi
elif [[ -z "${DEMO_USERNAME:-}" || -z "${DEMO_PASSWORD:-}" ]]; then
  echo "Both DEMO_USERNAME and DEMO_PASSWORD are required when overriding local demo credentials" >&2
  exit 1
fi

if [[ -z "${DEMO_MANAGER_USERNAME:-}" || -z "${DEMO_MANAGER_PASSWORD:-}" ]]; then
  DEMO_MANAGER_USERNAME="demo_manager"
  DEMO_MANAGER_PASSWORD="$(openssl rand -base64 24 | tr -d '\n')"
  (
    umask 077
    printf 'DEMO_MANAGER_USERNAME=%q\nDEMO_MANAGER_PASSWORD=%q\n' \
      "$DEMO_MANAGER_USERNAME" "$DEMO_MANAGER_PASSWORD" >> "$credentials_file"
  )
fi

export DEMO_USERNAME DEMO_PASSWORD DEMO_MANAGER_USERNAME DEMO_MANAGER_PASSWORD
password_hash="$(docker compose exec -T -e DEMO_PASSWORD api python -c '
from os import environ
from pwdlib import PasswordHash
print(PasswordHash.recommended().hash(environ["DEMO_PASSWORD"]))
')"
manager_password_hash="$(docker compose exec -T -e DEMO_MANAGER_PASSWORD api python -c '
from os import environ
from pwdlib import PasswordHash
print(PasswordHash.recommended().hash(environ["DEMO_MANAGER_PASSWORD"]))
')"

docker compose exec -T postgres psql -U "${POSTGRES_SUPERUSER:-postgres}" \
  -d "${POSTGRES_DB:-hidden_dissatisfaction}" -v ON_ERROR_STOP=1 \
  -v demo_username="$DEMO_USERNAME" \
  -v demo_password_hash="$password_hash" \
  -v demo_manager_username="$DEMO_MANAGER_USERNAME" \
  -v demo_manager_password_hash="$manager_password_hash" <<'SQL'
INSERT INTO app.users (username, password_hash, full_name, role, preferred_language)
VALUES (:'demo_username', :'demo_password_hash', 'Synthetic Demo Specialist', 'SPECIALIST', 'vi')
ON CONFLICT (username) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role,
    preferred_language = EXCLUDED.preferred_language,
    is_active = true;

INSERT INTO app.users (username, password_hash, full_name, role, preferred_language)
VALUES (:'demo_manager_username', :'demo_manager_password_hash', 'Synthetic Demo Manager', 'MANAGER', 'vi')
ON CONFLICT (username) DO UPDATE
SET password_hash = EXCLUDED.password_hash,
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role,
    preferred_language = EXCLUDED.preferred_language,
    is_active = true;

INSERT INTO ml.model_releases(
  model_release_id, release_version, model_name, model_version, model_artifact_uri,
  artifact_sha256, feature_schema_version, dataset_manifest_sha256, training_git_sha,
  source_snapshot_hash, training_run_id, aggregation_rule, evaluation_status
) VALUES (
  '00000000-0000-0000-0000-00000000d001', 'synthetic-demo-v1', 'synthetic-demo', 'v1',
  'demo://local/synthetic-demo-v1', repeat('0', 64), 'synthetic-demo-v1', repeat('1', 64),
  'synthetic-demo', 'synthetic-demo', '00000000-0000-0000-0000-00000000d010', 'max-v1', 'SYNTHETIC_DEMO'
) ON CONFLICT (release_version) DO NOTHING;

INSERT INTO ml.model_thresholds(model_release_id, threshold_version, medium_from, high_from, selection_policy)
VALUES ('00000000-0000-0000-0000-00000000d001', 'synthetic-demo-thresholds-v1', 0.40000000000000000, 0.70000000000000000, 'synthetic-demo')
ON CONFLICT DO NOTHING;

INSERT INTO ml.predictions(prediction_id, model_release_id, threshold_version, source_run_id,
  input_hash, model_input_hash, scored_at, state)
VALUES ('00000000-0000-0000-0000-00000000d002', '00000000-0000-0000-0000-00000000d001',
  'synthetic-demo-thresholds-v1', '00000000-0000-0000-0000-00000000d011', repeat('2', 64), repeat('3', 64), now(), 'READY')
ON CONFLICT (prediction_id) DO NOTHING;

UPDATE ml.predictions SET state = 'ACTIVE'
WHERE prediction_id = '00000000-0000-0000-0000-00000000d002' AND state = 'READY';

INSERT INTO ml.item_prediction_scores(prediction_id, order_id, order_item_id, product_item_id, score, risk_context, top_factors, synthetic, synthetic_metadata)
VALUES
('00000000-0000-0000-0000-00000000d002','demo-1001','001','demo-1001-001',0.91,'{"seller_id":"demo-seller-a","category":"electronics"}','["Late shipment signal","Repeated delivery delay"]',true,'{"fixture":"P12"}'),
('00000000-0000-0000-0000-00000000d002','demo-1002','001','demo-1002-001',0.78,'{"seller_id":"demo-seller-a","category":"home"}','["Payment friction","Long handling time"]',true,'{"fixture":"P12"}'),
('00000000-0000-0000-0000-00000000d002','demo-1003','001','demo-1003-001',0.63,'{"seller_id":"demo-seller-b","category":"beauty"}','["Delivery variance","Repeat contact"]',true,'{"fixture":"P12"}'),
('00000000-0000-0000-0000-00000000d002','demo-1004','001','demo-1004-001',0.54,'{"seller_id":"demo-seller-b","category":"toys"}','["Seller response delay"]',true,'{"fixture":"P12"}'),
('00000000-0000-0000-0000-00000000d002','demo-1005','001','demo-1005-001',0.82,'{"seller_id":"demo-seller-c","category":"sports"}','["High order value","Delivery exception"]',true,'{"fixture":"P12"}')
ON CONFLICT DO NOTHING;

INSERT INTO ml.order_prediction_scores(prediction_id, order_id, score, aggregation_rule, top_product_item_id, top_item_score, item_count, item_value, risk_context, top_factors, synthetic, synthetic_metadata)
SELECT prediction_id, order_id, score, 'max-v1', product_item_id, score, 1, 199.90, risk_context, top_factors, true, synthetic_metadata
FROM ml.item_prediction_scores WHERE prediction_id = '00000000-0000-0000-0000-00000000d002'
ON CONFLICT DO NOTHING;

INSERT INTO app.review_cases(order_id, prediction_id, aggregation_rule, status, assignee_id, original_queued_at, updated_at)
VALUES
('demo-1001','00000000-0000-0000-0000-00000000d002','max-v1','PENDING',NULL,now()-interval '1 hour',now()-interval '1 hour'),
('demo-1002','00000000-0000-0000-0000-00000000d002','max-v1','IN_PROGRESS',(SELECT user_id FROM app.users WHERE username=:'demo_username'),now()-interval '5 hours',now()-interval '30 minutes'),
('demo-1003','00000000-0000-0000-0000-00000000d002','max-v1','PENDING',NULL,now()-interval '26 hours',now()-interval '26 hours'),
('demo-1004','00000000-0000-0000-0000-00000000d002','max-v1','COMPLETED',(SELECT user_id FROM app.users WHERE username=:'demo_username'),now()-interval '2 days',now()-interval '1 day'),
('demo-1005','00000000-0000-0000-0000-00000000d002','max-v1','PENDING',NULL,now()-interval '3 hours',now()-interval '3 hours')
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO app.review_cycles(case_id, cycle_no, started_at, ended_at, sla_due_at, parameter_version)
SELECT c.case_id, 1, c.original_queued_at,
       CASE WHEN c.status = 'COMPLETED' THEN c.updated_at ELSE NULL END,
       c.original_queued_at + interval '24 hours', 'synthetic-demo-v1'
FROM app.review_cases c WHERE c.order_id LIKE 'demo-%'
ON CONFLICT (case_id, cycle_no) DO NOTHING;

INSERT INTO app.assignments(case_id, assignee_id, assigned_at)
SELECT c.case_id, c.assignee_id, c.original_queued_at + interval '1 hour'
FROM app.review_cases c WHERE c.status = 'IN_PROGRESS' AND c.assignee_id IS NOT NULL
ON CONFLICT DO NOTHING;

INSERT INTO app.case_comments(case_id, author_id, body)
SELECT c.case_id, (SELECT user_id FROM app.users WHERE username=:'demo_username'),
       'Synthetic demo note: customer contact is pending.'
FROM app.review_cases c WHERE c.order_id = 'demo-1002'
  AND NOT EXISTS (SELECT 1 FROM app.case_comments x WHERE x.case_id = c.case_id);
SQL
echo "Synthetic Specialist and Manager accounts plus full local demo dataset seeded."

revision="$(git rev-parse HEAD 2>/dev/null || printf 'unknown')"
generated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "$evidence_dir/P12-SYNTHETIC.txt" <<EOF
SYNTHETIC DEMO ONLY
This marker belongs to the P12 fixture workflow and is not Olist data.
No production or confirmatory ML performance is represented.
Command: make e2e
Revision: ${revision}
Generated at: ${generated_at}
EOF
echo "Synthetic demo marker written (no full-data ingestion)."

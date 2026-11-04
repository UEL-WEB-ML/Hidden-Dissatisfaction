# BA Bug Remediation and Re-score Lifecycle Plan

## Objective

Resolve the confirmed BA findings, preserve immutable prediction provenance, and make the demo and warehouse workflows reproducible.

## Approved Policies

- A review case remains bound to the prediction snapshot used when it was created.
- Superseding a prediction does not hide, close, re-score, or release an existing case.
- Open historical cases remain actionable and continue to count toward Specialist capacity.
- A later queue seed skips any order that already has a review case.
- Manager contact history is available in Order Detail; `attempt.html` remains Specialist-only.
- Manager Decisions are accepted only for `COMPLETED` and `SKIPPED` cases.
- Demo order IDs follow the public 32-character hexadecimal grammar.
- Parameter effective times sent by the UI are timezone-aware and at least one minute ahead.
- Logout remains client-side token removal in the thesis/demo scope.

## Delivery Steps

### 1. Workflow and frontend correctness

Files:
- `src/hidden_dissatisfaction/domain/workflow.py`
- `src/hidden_dissatisfaction/infrastructure/postgres_workflow_commands.py`
- `src/hidden_dissatisfaction/api/app.py`
- `src/hidden_dissatisfaction/application/queue.py`
- `src/hidden_dissatisfaction/infrastructure/postgres_risk_queue.py`
- `frontend/prototype/js/common.js`
- `frontend/prototype/html/decision.html`

Tasks:
- Reject Decisions for open cases with `409 INVALID_STATE`.
- Refresh a successful claim by exact internal order ID, never through public query validation.
- Serialize `datetime-local` values as timezone-aware ISO 8601.
- Send an omitted Decision due date as `null`.
- Hide the Decision form when a direct URL points to an ineligible case.

Exit criteria:
- Open-case Decision creates no decision or audit row.
- Claiming a non-public-grammar fixture ID returns 200 after one committed claim.
- Contact and parameter payloads contain timezone information.
- An empty Decision due date is accepted.

### 2. Queue contact count contract

Files:
- `src/hidden_dissatisfaction/application/queue.py`
- `src/hidden_dissatisfaction/infrastructure/postgres_risk_queue.py`
- `src/hidden_dissatisfaction/api/schemas.py`
- `BA/API_CONTRACT.md`

Tasks:
- Add non-null `contact_count` to `QueueOrder`.
- Calculate it in the queue SQL for the latest review cycle without N+1 requests.
- Carry it through queue, summary, claim response, and order detail schemas.

Exit criteria:
- New/current cycle starts at zero.
- Reopen resets the queue count to zero while preserving earlier cycle history.
- UI lists never render `undefined` for contact count.

### 3. Warehouse reproducibility

Files:
- `infra/jobs/Dockerfile`
- `compose.yaml`
- `Makefile`
- `README.md`

Tasks:
- Give UID 10001 writable dbt `logs` and `target` directories.
- Require and pass `DBT_SOURCE_RUN_ID` to every warehouse build.
- Document how the completed Bronze run ID is supplied.

Exit criteria:
- Missing run ID fails before dbt execution with a clear message.
- UID 10001 can create dbt logs and target artifacts.
- A valid completed run can execute `make warehouse`.

### 4. Historical prediction lifecycle

Files:
- `infra/postgres/migrations/V022__historical_case_prediction_visibility.sql`
- `src/hidden_dissatisfaction/infrastructure/postgres_queue_seeding.py`
- BA lifecycle documentation and PostgreSQL integration tests

Tasks:
- Expose active predictions plus exact superseded snapshots referenced by review cases.
- Require an ACTIVE prediction only when inserting a case, not on workflow updates.
- Preserve case identity, prediction ID, order uniqueness, raw ML-table revocations, and trigger security.
- Give the runtime seeder a narrow active-only seed view instead of raw ML-table access.

Exit criteria:
- An assigned case remains visible and actionable after its prediction is superseded.
- Capacity remains occupied until that case is closed.
- A new seed reports the old order as skipped and creates only genuinely new orders.
- Historical case reads still show the original model/score snapshot.

### 5. Demo and documentation alignment

Files:
- `scripts/demo-seed.sh`
- `BA/BRD.md`
- `BA/FRD.md`
- `BA/API_CONTRACT.md`
- `BA/TRACEABILITY.md`

Tasks:
- Replace `demo-*` order IDs with deterministic 32-character hexadecimal IDs.
- Record the approved re-score, contact-screen, Decision, effective-time, and logout policies.

Exit criteria:
- Demo search and claim follow the production API grammar.
- BA expected results match executable behavior.

## Verification

Focused gates:

```bash
uv run pytest tests/unit/test_workflow.py tests/unit/test_api_foundation.py tests/unit/test_api_schemas.py tests/unit/test_queue.py tests/contract/test_api_contract.py -q
node frontend/prototype/security-regression-check.js
```

Database gates:

```bash
uv run pytest tests/integration/test_postgres_workflow.py -q
```

Full gates:

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

## Rollback

- Application/frontend changes can be reverted independently before V022 is deployed.
- V022 is forward-only. If rollout fails, restore the previous views and guard in a new migration; never edit an applied migration.
- Do not mutate existing case prediction IDs or delete historical workflow data during rollback.

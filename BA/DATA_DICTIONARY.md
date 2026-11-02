# Data Dictionary — As-built PostgreSQL

Nguồn: schema runtime sau migration V001–V021. Kiểu `timestamp with time zone`
được viết gọn là `timestamptz`.

## 1. Schema `app`

### `app.users`

| Column | Type/null | Ghi chú |
|---|---|---|
| user_id | uuid, not null | PK, default UUID |
| username | varchar, not null | Unique |
| password_hash | text, not null | Argon2 qua `pwdlib` |
| full_name | varchar, not null | Tên hiển thị |
| role | varchar, not null | SPECIALIST/MANAGER |
| preferred_language | varchar, nullable | vi/en |
| is_active | boolean, not null | Default true |
| created_at | timestamptz, not null | Default now |

### `app.review_cases`

`case_id` PK; `order_id` unique; `prediction_id` FK; `aggregation_rule`;
`status`; `assignee_id`; `cycle_no`; `original_queued_at`; `outcome`;
`skip_reason`; `close_note`; `closed_at`; `reopen_count`; `updated_at`;
`row_version`.

Case snapshot guard không cho đổi `case_id`, `order_id`, `prediction_id`,
`aggregation_rule`, `original_queued_at` và yêu cầu prediction ACTIVE khi tạo.
`order_id` không có physical FK tới Gold.

### `app.review_cycles`

`cycle_id` PK; `case_id` FK; `cycle_no`; `started_at`; `ended_at`;
`reopen_reason`; `reopened_by`; `sla_due_at`; `parameter_version` nullable;
`parameter_bundle_id` nullable. Unique `(case_id,cycle_no)`.

### `app.assignments`

`assignment_id` PK; `case_id` FK; `assignee_id` FK; `assigned_at`;
`released_at`; `release_reason`. Partial unique index bảo đảm một assignment
chưa release cho mỗi case.

### `app.contact_attempts`

| Column group | Columns |
|---|---|
| Identity/links | `attempt_id`, `case_id`, `assignment_id`, `cycle_id` |
| Sequence | `attempt_no` (unique theo cycle qua index/constraint hiện hành) |
| Legacy compatibility | `channel`, `status`, `outcome` |
| Public workflow | `attempted_at`, `contact_result`, `note`, `next_contact_date`, `evidence_ref` |
| Audit | `created_by`, `created_at` |

`MESSAGE` ở API được lưu thành legacy channel `CHAT`. Bảng append-only.

### Evidence

- `app.evidence_uploads`: `upload_id`, `uploaded_by`, `storage_key`, `file_name`,
  `content_type`, `file_size`, `uploaded_at`, `attached_at`.
- `app.contact_evidence`: `evidence_id`, `case_id`, `attempt_id`, `storage_key`,
  `content_type`, `metadata`, `attached_at`, `expires_at`, `attached_by`.

Tên và kích thước file đã attach nằm trong `contact_evidence.metadata`.

### Comments và decisions

- `app.case_comments`: `comment_id`, `case_id`, `author_id`, `body`, `created_at`.
- `app.manager_decisions`: `decision_id`, `case_id`, `decided_by`, `decision`,
  `rationale`, `created_at`, `cycle_id`, `next_step`, `next_step_assignee_id`,
  `due_date`, `note`.

Hai bảng append-only. API map `body → text` và `rationale → reason`.

### Audit

- `app.audit_events`: `event_id`, `case_id`, `order_id`, `actor_id`, `provenance`,
  `event_type`, `old_value`, `new_value`, `reason`, `created_at`, `actor_kind`.
- `actor_kind`: USER/SYSTEM; USER cần actor ID, SYSTEM cần actor ID null.
- `provenance`: USER/SYSTEM/QUEUE_SEED.
- `app.audit_corrections`: `correction_id`, `event_id`, `corrected_by`,
  `correction`, `created_at`; append-only.

### Parameters

- `app.parameter_definitions`: `param_key` PK, `unit`, `min_value`, `max_value`,
  `allowed_values`, `in_brd`, `description`.
- `app.parameters`: `parameter_id` identity PK, `param_key`, `version`, `value`,
  `effective_at`, nullable `actor_id`, `reason`, `created_at`; unique key/version;
  append-only.
- `app.parameter_bundles`: `bundle_id`, `revision`, `parameter_id`, nullable
  `created_by`, `created_at`; append-only.
- `app.sla_adjustments`: `adjustment_id`, `cycle_id`, `sla_due_at`,
  `parameter_id`, `applied_at`.

API validation ranges trong domain là authoritative cho web requests; metadata
min/max seed cũ trong database rộng hơn ở một số key.

### Infrastructure

`app.schema_migrations(version, applied_at)` là migration ledger và được readiness
probe đọc để kiểm tra V021.

## 2. Schema `ml`

### `ml.model_releases`

| Column | Type/null |
|---|---|
| `model_release_id` | uuid, not null |
| `release_version` | text, not null |
| `model_name` | text, not null |
| `model_version` | text, not null |
| `model_artifact_uri` | text, not null |
| `artifact_sha256` | text, not null |
| `feature_schema_version` | text, not null |
| `dataset_manifest_sha256` | text, not null |
| `training_git_sha` | text, not null |
| `source_snapshot_hash` | text, not null |
| `training_run_id` | uuid, not null |
| `aggregation_rule` | text, not null |
| `evaluation_status` | text, not null |
| `created_at` | timestamptz, not null; default now |

### `ml.model_thresholds`

| Column | Type/null |
|---|---|
| `model_release_id` | uuid, not null; composite PK/FK |
| `threshold_version` | text, not null; composite PK |
| `medium_from` | numeric, not null |
| `high_from` | numeric, not null |
| `created_at` | timestamptz, not null; default now |
| `selection_policy` | text, not null; default `validation-f1-v1` |

### `ml.predictions`

| Column | Type/null |
|---|---|
| `prediction_id` | uuid, not null; PK |
| `model_release_id` | uuid, not null; FK |
| `threshold_version` | text, not null; FK cùng release |
| `source_run_id` | uuid, not null |
| `input_hash` | text, not null |
| `model_input_hash` | text, not null |
| `scored_at` | timestamptz, not null |
| `state` | text, not null |
| `created_at` | timestamptz, not null; default now |
| `activated_at` | timestamptz, nullable |

State là READY/ACTIVE/SUPERSEDED/REJECTED. Chỉ một prediction được ACTIVE.

### `ml.item_prediction_scores`

| Column | Type/null |
|---|---|
| `prediction_id` | uuid, not null; composite PK/FK |
| `order_id` | text, not null; composite PK |
| `order_item_id` | text, not null; composite PK |
| `product_item_id` | text, not null |
| `score` | numeric, not null |
| `risk_context` | jsonb, not null; default `{}` |
| `top_factors` | jsonb, not null; default `[]` |
| `synthetic` | boolean, not null; default false |
| `synthetic_metadata` | jsonb, not null; default `{}` |

### `ml.order_prediction_scores`

| Column | Type/null |
|---|---|
| `prediction_id` | uuid, not null; composite PK/FK |
| `order_id` | text, not null; composite PK |
| `score` | numeric, not null |
| `aggregation_rule` | text, not null |
| `top_product_item_id` | text, not null |
| `top_item_score` | numeric, not null |
| `item_count` | integer, not null |
| `item_value` | numeric, not null |
| `risk_context` | jsonb, not null; default `{}` |
| `top_factors` | jsonb, not null; default `[]` |
| `synthetic` | boolean, not null; default false |
| `synthetic_metadata` | jsonb, not null; default `{}` |

Order score phải bằng top item score qua FK/check.

### `ml.v_active_thresholds`

`threshold_version` text, `medium_from` numeric, `high_from` numeric và
`model_version` text; tất cả nullable theo metadata của view.

### `ml.v_risk_items_for_web`

`prediction_id` uuid; `order_id`, `order_item_id`, `product_item_id` text;
`risk_score` numeric; `risk_level`, `aggregation_rule` text; `top_factors` jsonb;
`synthetic` boolean; `synthetic_metadata`, `context` jsonb; `predicted_at`,
`scored_at` timestamptz; `model_release_id` uuid; `model_version`,
`threshold_version` text. Các cột đều nullable theo metadata của view.

### `ml.v_risk_orders_for_web`

`prediction_id` uuid; `order_id` text; `risk_score` numeric;
`top_product_item_id` text; `top_item_score` numeric; `item_count`, `items_count`
integer; `item_value` numeric; `risk_level`, `aggregation_rule` text;
`top_factors` jsonb; `synthetic` boolean; `synthetic_metadata`, `context` jsonb;
`predicted_at`, `scored_at` timestamptz; `model_release_id` uuid;
`model_version`, `threshold_version` text. Các cột đều nullable theo metadata
của view.

Commerce attributes không phải cột typed trong web views; chúng có thể nằm trong
`risk_context/context` JSONB. Public API hiện chỉ project seller/category và một
số metadata từ context.

## 3. Enum/check chính

| Field | Values |
|---|---|
| users.role | SPECIALIST, MANAGER |
| review_cases.status | PENDING, IN_PROGRESS, COMPLETED, SKIPPED |
| outcome | HAS_ISSUE, NO_ISSUE, DUPLICATE |
| skip_reason | UNREACHABLE, DUPLICATE, REFUSED, NOT_APPLICABLE, OTHER |
| contact_result | REACHED, NO_ANSWER, CALLBACK, WRONG_NUMBER |
| decision | NO_FURTHER_ACTION, FOLLOW_UP_CUSTOMER, WORK_WITH_SELLER, REFER_AFTER_SALES |
| prediction.state | READY, ACTIVE, SUPERSEDED, REJECTED |
| aggregation_rule | max-v1 |

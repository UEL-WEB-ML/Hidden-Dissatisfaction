# ERD — As-built

```mermaid
erDiagram
  USERS ||--o{ REVIEW_CASES : current_assignee
  USERS ||--o{ ASSIGNMENTS : assigned_to
  USERS ||--o{ CONTACT_ATTEMPTS : creates
  USERS ||--o{ CASE_COMMENTS : writes
  USERS ||--o{ MANAGER_DECISIONS : decides
  USERS ||--o{ AUDIT_EVENTS : acts
  USERS ||--o{ PARAMETERS : changes

  MODEL_RELEASES ||--o{ MODEL_THRESHOLDS : defines
  MODEL_RELEASES ||--o{ PREDICTIONS : runs
  MODEL_THRESHOLDS ||--o{ PREDICTIONS : selected_by
  PREDICTIONS ||--o{ ITEM_PREDICTION_SCORES : contains
  PREDICTIONS ||--o{ ORDER_PREDICTION_SCORES : contains
  ITEM_PREDICTION_SCORES ||--o{ ORDER_PREDICTION_SCORES : top_item_fk
  PREDICTIONS ||--o{ REVIEW_CASES : snapshot

  REVIEW_CASES ||--o{ REVIEW_CYCLES : has
  REVIEW_CASES ||--o{ ASSIGNMENTS : has
  REVIEW_CASES ||--o{ CONTACT_ATTEMPTS : has
  REVIEW_CASES ||--o{ CONTACT_EVIDENCE : owns
  REVIEW_CASES ||--o{ CASE_COMMENTS : has
  REVIEW_CASES ||--o{ MANAGER_DECISIONS : has
  REVIEW_CASES ||--o{ AUDIT_EVENTS : audited_by

  REVIEW_CYCLES ||--o{ CONTACT_ATTEMPTS : scopes
  REVIEW_CYCLES ||--o{ MANAGER_DECISIONS : scopes
  REVIEW_CYCLES ||--o{ SLA_ADJUSTMENTS : adjusted_by
  ASSIGNMENTS ||--o{ CONTACT_ATTEMPTS : assignment_context
  CONTACT_ATTEMPTS ||--o{ CONTACT_EVIDENCE : attaches
  AUDIT_EVENTS ||--o{ AUDIT_CORRECTIONS : corrected_by

  PARAMETER_DEFINITIONS ||--o{ PARAMETERS : versions
  PARAMETERS ||--o{ PARAMETER_BUNDLES : bundled
  PARAMETERS ||--o{ SLA_ADJUSTMENTS : source
  PARAMETER_BUNDLES ||--o{ REVIEW_CYCLES : snapshot
```

## Bất biến vật lý đáng chú ý

- `review_cases.order_id` unique: một workflow case cho mỗi order.
- `(review_cycles.case_id,cycle_no)` unique.
- Một assignment active/case qua partial unique index `released_at IS NULL`.
- Parameter, audit, attempts, evidence, comments, decisions và corrections là
  append-only bằng trigger và/hoặc DB grants.
- Prediction score rows và model releases immutable.
- Một prediction snapshot ACTIVE tại một thời điểm.
- Review case không được đổi order/prediction/aggregation/original queue snapshot.
- Queue seed audit phải dùng actor SYSTEM và event type QUEUE_SEED.

## Lưu ý legacy

`contact_attempts` giữ cả bộ cột P7 (`channel`, `status`, `outcome`) và bộ cột API
v0.5 bổ sung (`cycle_id`, `contact_result`, `note`, `next_contact_date`,
`evidence_ref`). Đây là schema tương thích ngược, chưa được chuẩn hóa thành một bộ
cột duy nhất.

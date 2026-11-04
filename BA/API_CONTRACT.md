# API Contract — As-built

## 1. Quy ước

- Base path: `/api/v1`.
- Authentication: `Authorization: Bearer <JWT>`; cookie mode chưa hoạt động.
- JSON dùng `snake_case`; datetime response là ISO 8601 có timezone.
- List Queue mặc định `limit=20`, tối đa 100.
- Lỗi HTTP do ứng dụng xử lý có dạng:

```json
{"error":{"code":"VALIDATION_ERROR","message":"Validation error","details":null}}
```

Unhandled 500 chưa được đảm bảo cùng envelope. Logout là stateless `204`; token
không có denylist và còn hiệu lực tới khi hết hạn.

## 2. Bảng mã

| Nhóm | Giá trị |
|---|---|
| role | `SPECIALIST`, `MANAGER` |
| risk level | `HIGH`, `MEDIUM`, `LOW` |
| case status | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`; query thêm `OPEN` |
| outcome | `HAS_ISSUE`, `NO_ISSUE`, `DUPLICATE` |
| skip reason | `UNREACHABLE`, `DUPLICATE`, `REFUSED`, `NOT_APPLICABLE`, `OTHER` |
| contact method | `PHONE`, `EMAIL`, `MESSAGE` |
| contact result | `REACHED`, `NO_ANSWER`, `CALLBACK`, `WRONG_NUMBER` |
| decision | `NO_FURTHER_ACTION`, `FOLLOW_UP_CUSTOMER`, `WORK_WITH_SELLER`, `REFER_AFTER_SALES` |
| sort | `priority`, `sla`, `aging` |
| SLA filter | `over`, `soon`, `esc`, `stale` |

## 3. Public DTO

### User

`user_id`, `username`, `full_name`, `role`, `preferred_language`, `created_at`,
`active_count`, `capacity`, `slots_left`. Workload fields có thể null với Manager.

### QueueOrder

`order_id`, `risk_score`, `risk_level`, `status`, `assignee_id`, `assignee_name`,
`queued_at`, `original_queued_at`, `sla_due_at`, `matched_item_id`, `top_item`,
`top_factors`, `items_count`, `outcome`, `skip_reason`, `self_claim_allowed`,
`contact_count` (số lần liên lạc trong cycle mới nhất, integer mặc định `0`),
`sla_state`, `sla_hours_left`, `aging_hours`, `total_aging_hours`, `is_escalated`,
`is_stale`.

### TopItem / ItemDetail

`product_item_id`, `category`, `risk_score`, `risk_level`, `top_factors`,
`synthetic_data_flag`, `model_version`, `predicted_at`, `data_source`,
`threshold_version`, `aggregation_rule`.

### OrderDetail

```text
order: QueueOrder + case_id, aggregation_rule, model_version, predicted_at,
       threshold_version, seller_id, category, cycle_no, updated_at, closed_at,
       reopen_count, needs_decision, has_synthetic_item, items
cycles, contacts, comments, decisions, next_step, model_notes,
audit_events, status_history, seller_open_count
```

## 4. Endpoint

| Method/path | Quyền | Request | Response chính |
|---|---|---|---|
| `POST /auth/login` | Public | username, password (8–256 chars) | token, user |
| `POST /auth/logout` | Auth | – | 204 |
| `GET /auth/me` | Auth | – | User |
| `PATCH /auth/me` | Auth | preferred_language | User |
| `GET /config` | Auth | – | effective config |
| `GET /parameters` | Manager | – | items + history |
| `POST /parameters` | Manager | key, value, effective_at, reason | created version |
| `GET /users` | Auth | optional role | `{items:[User]}` |
| `GET /orders` | Auth | Queue filters | QueuePage |
| `GET /orders/summary` | Auth | – | counters, first_pending, me |
| `GET /orders/filter-options` | Auth | – | sellers, categories |
| `GET /orders/{order_id}` | Auth | – | OrderDetail |
| `POST /orders/{order_id}/claim` | Specialist | – | order, me |
| `POST /orders/{order_id}/assign` | Manager | assignee_id, reason?, override_capacity | order, previous assignee |
| `POST /orders/{order_id}/complete` | Holder/Manager | outcome, note? | order |
| `POST /orders/{order_id}/skip` | Holder/Manager | reason, note? | order |
| `POST /orders/{order_id}/reopen` | Manager | reason?, review_confirmed | order |
| `POST /orders/{order_id}/comments` | Holder/Manager | text | comment |
| `POST /orders/{order_id}/model-notes` | Manager | note | model note |
| `POST /orders/{order_id}/contacts` | Holder Specialist | ContactBody | contact, order |
| `POST /orders/{order_id}/decisions` | Manager | DecisionBody | decision, order |
| `POST /files` | Specialist | multipart `file` | file metadata + URL |
| `GET /files/{file_id}` | Owner/Manager | – | file stream |
| `GET /dashboard` | Manager | dashboard filters | dashboard projection |
| `GET /audit-events` | Manager | audit filters | items,total,all_total |

Health routes ngoài prefix: `/health`, `/health/live`, `/health/ready`.

`contacted_at` và `effective_at` dùng ISO 8601 có timezone. `due_date` trong
DecisionBody là ngày hoặc `null`. Decision trên case chưa đóng trả
`409 INVALID_STATE`.

## 5. Queue query

| Query | Validation/ý nghĩa |
|---|---|
| `q` | hex order prefix hoặc `<hex-order>-<positive item no>` |
| `level` | HIGH/MEDIUM/LOW |
| `status` | PENDING/IN_PROGRESS/COMPLETED/SKIPPED/OPEN; mặc định OPEN |
| `assignee` | UUID, `me`, hoặc `none` |
| `smin`, `smax` | 0–1, min không lớn hơn max |
| `from`, `to` | datetime, from không sau to |
| `seller`, `category` | exact context match |
| `outcome` | `O:<outcome>` hoặc `S:<skip_reason>` |
| `sla` | over/soon/esc/stale |
| `needs_decision` | boolean |
| `sort` | priority/sla/aging |
| `limit`, `offset` | 1–100, offset >= 0 |

Invalid query hiện trả `422 VALIDATION_ERROR`.

## 6. Config và parameter response

`GET /config` trả đúng các key:

`parameter_version`, `threshold_version`, `medium_from`, `high_from`,
`sla_calendar`, `sla_hours.{HIGH,MEDIUM,LOW}`, `first_touch_hours`, `capacity`,
`capacity_warn`, `max_contact`, `retry_gap_days`, `soon_hours`, `stale_hours`,
`aging_days`, `reopen_review_days`, `reopen_review_times`, `server_time`.

Không có `typical_order`.

`GET /parameters` trả `parameter_version`, `server_time`, `items`, `history`.
Current item có thêm `updated_by_name` và `scheduled`.

## 7. Dashboard response

Order view trả:

- `as_of`, `from`, `view`;
- `totals`: cases/open/pending/in_progress/completed/skipped/overdue/escalated/stale/needs_decision;
- `rates`: closed/overdue/high;
- `by_level` object, `score_bands` list;
- `by_seller`, `by_category`, `workload`, `attention`, `recent_overrides`;
- `service`, `actions`, `trend`.

Product view thêm `product.{totals,by_category,top_items}`.

## 8. Known contract quirks

- Audit read model hiện trả `provenance AS actor_kind`; queue seed có thể trả
  `actor_kind="QUEUE_SEED"` dù DB `actor_kind` thật là `SYSTEM`.
- `status_history` hiện không gồm `DECISION`.
- `GET /parameters.parameter_version` là `current`, còn `/config` dùng `bundle-N`.
- POST parameter response chưa có `old_value` và actor name.
- Error localization chưa áp dụng cho mọi policy error.
- Nhiều dict response chưa có typed OpenAPI schema chi tiết.

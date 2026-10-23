# ERD – WEB OLIST HIDDEN DISSATISFACTION

## 1. Phạm vi P7

P7 seed baseline tối thiểu gồm đúng sáu bảng trong schema `app`: `users`,
`review_cases`, `review_cycles`, `parameter_definitions`, `parameters` và
`audit_events`. Đây là logical ERD, không phải migration.

```text
app.users (user_id PK) 1───< review_cases (assignee_id)
app.users 1───< review_cycles (reopened_by)
app.users 1───< parameters (actor_id)
app.users 1───< audit_events (actor_id, USER only)
review_cases (case_id PK) 1───< review_cycles (case_id)
review_cases 1───< audit_events (case_id, nullable)
parameter_definitions (param_key PK) 1───< parameters (param_key)
```

`review_cases` là grain một order risk case (`order_id` UNIQUE). Một
`review_cycle` là một lần vào queue/mở lại; `(case_id, cycle_no)` UNIQUE.
`parameters` là một phiên bản của một parameter key; `(param_key, version)`
UNIQUE. `audit_events` là sự kiện append-only.

## 2. Ràng buộc, bất biến, sở hữu và truy cập

- UUID dùng cho thực thể; `event_id` và `parameter_id` dùng identity. FK phải
  trỏ tới bản ghi tồn tại; case được tắt/lưu lịch sử, không xoá user.
- `parameter_definitions` là danh mục tĩnh do nhóm phát triển sở hữu; chỉ
  Manager quản lý `parameters`. Backend sở hữu current state của case/cycle.
- `parameters` và `audit_events` chỉ INSERT/SELECT, không UPDATE/DELETE.
  Mọi cập nhật nghiệp vụ tạo audit trong cùng transaction.
- Ứng dụng truy cập qua Backend, kiểm tra role/ownership; audit chỉ Manager
  đọc theo API contract.

`audit_events.actor_kind` là `USER|SYSTEM`. `USER` bắt buộc `actor_id` FK
tới `app.users`; `SYSTEM` bắt buộc `actor_id = NULL`. Queue seed dùng
`event_type = QUEUE_SEED` và `reason` ghi source/batch provenance.

## 3. Planned/deferred

`assignments`, `contact_attempts`, `contact_evidence`, `case_comments`,
`manager_decisions` và các bảng workflow khác là **planned/deferred**, chưa
thuộc P7 seed baseline và không được suy ra thành migration từ ERD này.

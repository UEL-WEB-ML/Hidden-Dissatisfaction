# Business Requirements Document — As-built

## 1. Mục tiêu hệ thống

Hệ thống hỗ trợ Specialist và Manager xem các order risk case, ưu tiên xử lý,
ghi nhận liên lạc khách hàng, đóng hoặc mở lại case, đưa ra quyết định quản lý,
quản lý tham số vận hành và truy vết audit. Risk score là dữ liệu chỉ đọc từ
prediction snapshot; người dùng nghiệp vụ không được sửa score hoặc risk level.

## 2. Actor và quyền

| Khả năng | Specialist | Manager |
|---|---:|---:|
| Đăng nhập, đổi ngôn ngữ, xem hồ sơ | Có | Có |
| Xem Risk Queue và Order Detail | Có | Có |
| Claim case | Chỉ `PENDING`, chưa giao, LOW/MEDIUM và còn capacity | Không |
| Thêm Contact Attempt | Chỉ case `IN_PROGRESS` đang được giao | Không |
| Complete/Skip | Case được giao | Có thể thực hiện theo policy backend |
| Dashboard | Không | Có |
| Assign/Reassign, capacity override | Không | Có |
| Reopen, model note, Manager Decision | Không | Có |
| Audit History, Parameter Settings | Không | Có |

Frontend ẩn màn/action ngoài quyền. Backend vẫn kiểm tra role và ownership độc lập.

## 3. Phạm vi chức năng hiện có

1. Bearer-token authentication và user preference `vi|en`.
2. Risk Queue: filter, sort, pagination, summary và claim.
3. Order Detail: prediction metadata, item risk output, cycle, attempts, comments,
   decisions, next step, status history và audit cho Manager.
4. Manager assignment/reassignment, capacity override và reopen.
5. Contact Attempt append-only, tối đa ba evidence PNG/JPG/PDF, mỗi file tối đa 5 MB.
6. Complete/Skip và auto-skip `UNREACHABLE` sau lần liên lạc thất bại cuối cùng.
7. Manager Dashboard theo order hoặc product item.
8. Manager Decision append-only.
9. Audit History chỉ đọc.
10. Parameter version append-only, hỗ trợ effective time trong tương lai.
11. Giao diện tiếng Việt/Anh.

## 4. Workflow case

```text
PENDING --claim/assign--> IN_PROGRESS --complete--> COMPLETED
                                    \--skip------> SKIPPED
COMPLETED/SKIPPED --Manager reopen--> PENDING (cycle mới)
```

- Complete/Skip chỉ hợp lệ từ `IN_PROGRESS`.
- `COMPLETED` bắt buộc một outcome: `HAS_ISSUE`, `NO_ISSUE`, `DUPLICATE`.
- `SKIPPED` bắt buộc một reason: `UNREACHABLE`, `DUPLICATE`, `REFUSED`,
  `NOT_APPLICABLE`, `OTHER`; `OTHER` bắt buộc note.
- Reopen chỉ dành cho Manager. Nếu case đóng lâu hơn `reopen_review_days` hoặc
  số lần reopen đạt `reopen_review_times`, request phải có `review_confirmed=true`.
- Mỗi reopen tạo review cycle mới, giữ `original_queued_at` và lịch sử cũ.

## 5. Claim, assignment và capacity

- Specialist không được claim HIGH.
- Claim dùng conditional update/row version để tránh hai người cùng nhận.
- Capacity lấy từ parameter đang hiệu lực.
- Reassign bắt buộc reason.
- Assign vượt capacity bắt buộc `override_capacity=true` và reason; backend tạo
  audit override.
- Mỗi case chỉ có một assignment chưa `released_at`.

## 6. Contact Attempt và evidence

- Method: `PHONE`, `EMAIL`, `MESSAGE`.
- Result: `REACHED`, `NO_ANSWER`, `CALLBACK`, `WRONG_NUMBER`.
- `contacted_at` phải có timezone và không ở tương lai.
- `next_contact_date`, nếu có, không được trước ngày contact.
- Bộ đếm attempt tính theo current cycle và không vượt `max_contact`.
- Lần cuối không `REACHED` đóng nguyên tử case thành `SKIPPED/UNREACHABLE`.
- Evidence upload trước, sau đó gắn bằng `file_id`; một upload chỉ được dùng một lần.

## 7. Manager Decision và comment

- Decision code: `NO_FURTHER_ACTION`, `FOLLOW_UP_CUSTOMER`, `WORK_WITH_SELLER`,
  `REFER_AFTER_SALES`.
- Decision, reason và next step bắt buộc theo domain policy; due date không ở quá khứ.
- Decision và comment chỉ thêm mới, không có API sửa/xóa.
- Comment dài 1–1000 ký tự và chỉ người giữ case hoặc Manager được thêm.

## 8. Parameter Configuration

Các key hiện có:

`sla_calendar`, `sla_hours_high`, `sla_hours_medium`, `sla_hours_low`,
`first_touch_hours`, `soon_hours`, `stale_hours`, `capacity`, `capacity_warn`,
`max_contact`, `retry_gap_days`, `aging_days`, `reopen_review_days`,
`reopen_review_times`.

- Version mới là append-only, cần effective time và reason.
- `capacity_warn < capacity`.
- Enum `sla_calendar`: `CALENDAR|BUSINESS_HOURS`.
- Hours: 1–720; days: 1–60; orders: 1–20; times: 1–10.
- Giá trị hiện hành là version mới nhất có `effective_at <= now`.
- SLA cycle được ghi khi seed/reopen. Thay đổi SLA cho cycle đang mở chỉ được áp
  dụng khi chạy job `recalculate-sla`; chưa có scheduler tự chạy job này.

## 9. Prediction và dữ liệu ML

- Item score được lưu trong immutable prediction snapshot.
- Order score dùng `max-v1`, bằng item score cao nhất.
- Chỉ một prediction snapshot có state `ACTIVE`.
- Threshold LOW/MEDIUM/HIGH đi cùng model release.
- Workflow case giữ `prediction_id` và `aggregation_rule` từ lúc tạo.

## 10. Ngoài phạm vi hoặc chưa hoàn thiện

- Realtime commerce integration.
- Online/incremental training và auto-retrain.
- Model registry/promotion/rollback tự động.
- Token denylist/revocation; logout hiện chỉ xóa token phía client.
- Business-hours SLA thật; backend hiện cộng elapsed hours.
- Backend first-touch SLA enforcement.
- Backend tự áp `retry_gap_days`; frontend chỉ đề xuất ngày.
- `suggested_action` và đầy đủ commerce context chưa nằm trong public Order DTO.
- Tạo/xóa parameter definition, rollback version, import/export configuration.

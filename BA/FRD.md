# Functional Requirements Document — As-built

## 1. Màn hình và quyền

| Màn hình | File | Specialist | Manager | Backend chính |
|---|---|---:|---:|---|
| Login | `login.html` | Có | Có | `/auth/login`, `/auth/me` |
| Risk Queue | `index.html` | Có | Có | `/orders`, `/orders/summary` |
| Order Detail | `order.html` | Có | Có | `/orders/{order_id}` và workflow actions |
| Contact Attempts | `attempt.html` | Có | Không | `/contacts`, `/files` |
| Dashboard | `overview.html` | Không | Có | `/dashboard` |
| Decisions | `decision.html` | Không | Có | closed orders, `/decisions` |
| Audit History | `audit.html` | Không | Có | `/audit-events` |
| Parameter Settings | `settings.html` | Không | Có | `/parameters`, `/config` |
| Profile | `profile.html` | Có | Có | `/auth/me`, `/config` |

## 2. Risk Queue

### Hành vi

- Default status là `OPEN` (`PENDING + IN_PROGRESS`).
- Filter: order/product-item query, level, status, assignee, score range, queue
  time, seller, category, outcome, SLA và needs-decision.
- Sort: `priority`, `sla`, `aging`; phân trang `limit/offset`.
- Priority mặc định: score giảm, SLA gần trước, queue lâu trước.
- Specialist thấy claim cho LOW/MEDIUM pending khi còn slot; HIGH chờ Manager assign.

### Acceptance as-built

- API trả `{items,total,limit,offset}`.
- Một order chỉ một dòng.
- Product Item ID match trả `matched_item_id`.
- Invalid filter trả `422 VALIDATION_ERROR`.

## 3. Order Detail

Hiển thị các field public hiện có trong `OrderDetailOrder`: trạng thái, score/level,
top item, top factors, model/threshold version, seller/category, SLA/aging,
assignee, cycle, contacts, comments, decisions, next step và history.

Không yêu cầu UI hiển thị các field backend chưa trả: customer city/state, order
timeline, order value/freight, item product/price/weight/photos và suggested action.

Manager nhận `audit_events`; Specialist nhận `audit_events=null`.

## 4. Claim và assignment

- Claim chỉ Specialist; backend kiểm tra state, risk level và capacity.
- Manager assign/reassign bằng Specialist ID.
- Reassign hoặc override bắt buộc reason.
- Sau thao tác, UI reload Order/User/Queue để đồng bộ active count và slot.

## 5. Complete, Skip và Reopen

- Complete form yêu cầu outcome hợp lệ.
- Skip form yêu cầu reason; `OTHER` yêu cầu note.
- Manager có thể reopen closed case với reason; confirmation xuất hiện khi policy yêu cầu.
- Reopen tạo cycle mới và đưa case về `PENDING`, chưa assignee.

## 6. Contact Attempts

- Trang chỉ tải case `IN_PROGRESS` của Specialist hiện tại.
- Manager không mở trang Contact Attempts; lịch sử contact cần cho Decision được
  hiển thị read-only ngay trong Order Detail và Decisions.
- Form gồm contacted time, method, result, note, next-contact date, evidence ref.
- Upload tối đa ba file; API kiểm tra magic bytes thay vì tin MIME từ client.
- Frontend đề xuất next-contact date bằng `retry_gap_days` business days.
- Backend chỉ kiểm tra ngày không trước contact; chưa enforce đúng retry interval.

## 7. Dashboard

- Chỉ Manager.
- Filter: `days=1|3|7`, level, seller, category, assignee, status, product item.
- View `order|product`.
- Response thực có totals, rates, by-level, score bands, seller/category groups,
  workload, attention, service, actions, trend và product block khi cần.
- Frontend dùng `normalizeDashboard()` để chuẩn hóa DTO backend trước khi render.

## 8. Decisions

- Danh sách được ghép từ hai query `COMPLETED` và `SKIPPED` có
  `needs_decision=true`.
- Manager xem detail, attempts/comments/previous decisions và ghi decision mới.
- API chỉ nhận decision khi case đang `COMPLETED` hoặc `SKIPPED`; form chỉ hiện
  cho case đóng đang có `needs_decision=true`.
- Decision append-only; decision mới nhất trở thành `next_step` summary.

## 9. Audit History

- Chỉ Manager.
- Filter theo event type, actor, order prefix và override-only.
- Phân trang, read-only.
- As-built caveat: read projection hiện map `provenance` sang `actor_kind`; queue
  seed vì vậy có thể trả `actor_kind="QUEUE_SEED"`.

## 10. Parameter Settings

- Hiển thị 14 parameter, current value, version, effective time, actor, scheduled
  versions và history.
- Manager tạo version mới; không sửa/xóa version cũ.
- UI gửi thời gian ISO 8601 có timezone và mặc định thời điểm hiệu lực sớm nhất
  là một phút sau `server_time` để tránh race với validation phía server.
- UI không hỗ trợ thêm/xóa parameter definition, cancel schedule hay rollback nhanh.

## 11. Language và lỗi

- Ngôn ngữ lưu ở local storage và `preferred_language` của user.
- Frontend dịch label/status; ID, code, score và user-entered text không đổi.
- Validation request có message vi/en; policy error backend hiện chủ yếu là tiếng Anh.
- Frontend xử lý error envelope `{error:{code,message,details}}` và network error.

## 12. Non-functional behavior hiện có

- Same-origin frontend proxy tới `/api/v1`.
- PostgreSQL readiness kiểm tra migration ledger V022.
- Evidence lưu ngoài database; metadata và ownership nằm trong PostgreSQL.
- Domain/application test coverage gate 100%; static/security frontend checks có trong CI.
- Không có browser automation E2E được tuyên bố; walkthrough hiện là authenticated API flow.

# Báo cáo kiểm thử BA theo role: Manager và Specialist

**Ngày:** 2026-11-04  
**Môi trường:** Docker local, `http://localhost:4200`, API/PostgreSQL local.  
**Dữ liệu:** synthetic demo fixture, không phải model inference hay đánh giá Olist.

## Mục tiêu và cách test

Đối chiếu web/API với `BA/BRD.md`, `BA/FRD.md`, `BA/API_CONTRACT.md` và `BA/TRACEABILITY.md`.

1. Kiểm tra navigation, screen, queue/filter, form, feedback và URL query.
2. Test có kiểm soát trên fixture: claim một case MEDIUM và complete case đó.
3. Khi thấy sai khác, đối chiếu frontend, API route, domain policy và query projection.
4. Không thay đổi parameter; không tạo decision/contact/evidence thành công; không assign/reassign.

## Kết quả Manager

| Test | Output | Kết quả |
|---|---|---|
| Navigation | Có Dashboard, Queue, Detail, Decisions, Audit, Settings; Contact Attempts không có trong nav. | Pass |
| Dashboard | Có order/product switch, HIGH chưa giao, SLA, workload, service metrics, action links. | Pass |
| Queue/filter | Chọn `HIGH` tạo URL `?level=HIGH`, chỉ còn 3 HIGH cases. | Pass |
| Assignment UI | HIGH pending có `Giao đơn`; case in-progress có `Chuyển người`. | Pass |
| Detail model | Score/level chỉ đọc, có `max-v1`, version và synthetic warning. | Pass |
| Settings/Audit | Có 14 key/version/history và audit filters read-only. | Pass |
| Decision eligibility | `decision.html?id=demo-1001` với case `PENDING` vẫn hiện form lưu Decision. | **Fail P1** |
| Decision list | Case đóng hiển thị `undefined/3 lần liên lạc`. | **Fail P2** |
| Contact direct link | Manager mở được `attempt.html` read-only, khác FRD matrix. | **Mismatch P2** |

## Kết quả Specialist

| Test | Output | Kết quả |
|---|---|---|
| Navigation | Chỉ thấy Queue, Detail, Contact Attempts. | Pass |
| HIGH restriction | HIGH pending hiện `Chờ Manager giao`, không có claim action. | Pass |
| Claim MEDIUM | `demo-1003` thành `IN_PROGRESS`, workload `1/5 → 2/5`, nhưng UI báo `Request failed (500)`. | **Fail P1** |
| Contact worklist | Form contact có sẵn, nhưng list hiển thị `undefined/3`. | **Fail P2** |
| Contact default time | Submit default datetime nhận `contacted_at must not be in the future`. | **Fail P1** |
| Complete validation | Bỏ outcome: `Chọn kết quả trước khi hoàn tất.` | Pass |
| Complete success | `NO_ISSUE` đóng `demo-1003`, trả slot và có history actor/outcome. | Pass |

## Sai khác và khuyến nghị

### P1 — Decision được phép cho case đang mở

**Nguyên nhân:** `decision.html` render form cho direct ID mọi state; `PostgresWorkflowCommands.add_decision()` không kiểm tra state.  
**Sửa:** Backend chỉ cho `COMPLETED`/`SKIPPED`, trả `409 INVALID_STATE` còn lại. Frontend chỉ show form/link khi `isClosed(order) && order.needs_decision`. Thêm unit, integration và browser test direct URL.

### P1 — Claim commit thành công nhưng response trả 500

**Nguyên nhân:** Sau commit, endpoint đọc lại bằng `q=demo-1003`; public queue validator chỉ chấp nhận ID/prefix hexadecimal, không chấp nhận `demo-*`.  
**Sửa:** Dựng response claim bằng exact-order-ID internal query, không tái dùng public `q` grammar; hoặc chính thức hỗ trợ fixture ID. Thêm integration test claim synthetic case phải trả 200 và không commit nếu response build thất bại.

### P1 — Contact Attempt gửi datetime không có timezone

**Nguyên nhân:** `apiTime()` đổi `datetime-local` thành `YYYY-MM-DD HH:mm`, trong khi backend bắt datetime timezone-aware.  
**Sửa:** Gửi ISO 8601 có timezone, ví dụ `new Date(localDatetimeValue).toISOString()`. Giữ backend validation; cập nhật comment/wire format cũ; thêm browser test submit default time thành công.

### P2 — Queue API không trả `contact_count`

**Nguyên nhân:** `GET /orders`/`QueueOrder` thiếu field, nhưng Decisions và Contact Attempts đọc `c.contact_count`.  
**Sửa:** Thêm current-cycle `contact_count` integer default 0 vào queue projection, Pydantic DTO, API Contract và contract tests. Tránh N+1 detail request; thêm browser assertion không có text `undefined`.

### P2 — Quyền xem Contact Attempts của Manager chưa thống nhất

**Nguyên nhân:** FRD §1 ghi Manager không có screen này, còn direct link và Decision cho Manager mở read-only history.  
**Sửa khuyến nghị:** Sửa BA thành **Manager: read-only; Specialist: create contact attempt**, vì Manager cần history để quyết định. Nếu cấm tuyệt đối, thêm client guard, bỏ direct link, chỉ giữ history trong Order Detail.

## Dữ liệu demo đã thay đổi

- `demo-1003`: Specialist claim, sau đó complete với `NO_ISSUE`.
- Hai thao tác tạo audit/status-history record.
- Không có contact attempt, decision, parameter version, assignment/reassignment hay evidence upload thành công.


## Kết luận

Role gating hiển thị, HIGH restriction, queue filtering, immutable model display, parameter UI và complete-with-outcome khớp BA. Ưu tiên sửa ba P1 trước walkthrough runtime: Decision sai state, claim demo 500 sau commit, Contact Attempt không submit được.


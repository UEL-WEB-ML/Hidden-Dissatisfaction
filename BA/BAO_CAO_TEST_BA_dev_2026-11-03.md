# Test nhánh `dev` theo thư mục BA — 03/11/2026

- Repo: `UEL-WEB-ML/Hidden-Dissatisfaction`, nhánh `dev`, commit `54a8d92`
- Môi trường: `make start` + `make demo-seed` trên máy local (5 đơn giả lập `demo-1001…1005`), thêm 1 Specialist test để kiểm giao/giao lại
- Nguồn ca test: `BA/BRD.md`, `BA/FRD.md`, `BA/API_CONTRACT.md`, `BA/TRACEABILITY.md` (mục nào ghi ở cột Mục BA)

## Tổng quan

| Bộ kiểm | Kết quả |
|---|---|
| Bộ có sẵn của repo: `tests/smoke.sh` | Pass |
| Bộ có sẵn của repo: `tests/demo_e2e.sh` (walkthrough 2 vai) | Pass |
| Bộ có sẵn của repo: pytest unit + contract | 199/199 pass |
| Ca test viết theo BA (gọi API thật) | **124/127 pass**, 3 fail |
| Kiểm lại trên giao diện (Playwright) | Tái hiện được 2 lỗi trên UI |
| Vòng 2 — dbt build trên Olist thật | 122/122 PASS (sau khi vượt lỗi 4, 5) |
| Vòng 2 — ca test theo BA với 100 đơn Olist thật | 127/128 pass |
| Vòng 3 — bấm giao diện theo FRD (Trúc bấm tay + script 20 bước) | 18/20 bước đúng; thêm lỗi 7 (nặng) và lỗi 8 |

## Lỗi tìm được

### 1. Nhận case báo lỗi 500 dù đã nhận thành công (nặng khi demo; với mã Olist thật không bị, xem vòng 2)
- **Ca:** CL-02. **Mục BA:** BRD §2 và §4, FRD §4.
- **Làm:** Specialist bấm **Nhận** ở đơn MEDIUM `demo-1003`.
- **Mong đợi:** 200, case chuyển `IN_PROGRESS`, UI cập nhật số slot.
- **Thực tế:** API trả **500**, UI hiện toast `Request failed (500).` Nhưng DB đã ghi nhận case `IN_PROGRESS` với assignee là người bấm, tải lại trang thì thấy đã nhận.
- **Nguyên nhân:** trong `src/hidden_dissatisfaction/api/app.py:452`, sau khi claim xong, code gọi `list_orders(QueueFilters(query=order_id))` để đọc lại đơn. Bộ lọc `q` chỉ nhận mã hex (`domain/queue.py:16`), mà mã demo là `demo-1003`, nên ném `QueueQueryValidationError` và bị trả thành 500.
- **Phạm vi:** chỉ endpoint claim (assign, complete… không dùng cách này). Với mã Olist thật (32 ký tự hex) thì không lỗi, nhưng bản demo đem đi trình bày thì lỗi.
- **Ảnh:** `shots/ui-claim-500.png`

### 2. Danh sách hiện `undefined/3` lần liên lạc
- **Ca:** QU-06. **Mục BA:** API §3 QueueOrder, FRD §6 và §8.
- **Thực tế:** `attempt.html:56` và `decision.html:56` đọc `c.contact_count` từ `GET /orders`, nhưng QueueOrder (cả code lẫn API contract) không có field này. Field này chỉ nằm trong OrderDetail.
- **Sửa:** thêm `contact_count` vào QueueOrder (cập nhật luôn `BA/API_CONTRACT.md`), hoặc UI lấy từ chỗ khác.

### 3. Không tìm được đơn demo theo mã
- **Ca:** QU-14. **Mục BA:** API §5 (`q` = hex order prefix).
- **Thực tế:** gõ `demo-1001` vào ô tìm thì UI báo sai định dạng; gọi API trả 422. Mã demo không theo định dạng mà contract yêu cầu.
- Cùng nguồn gốc với lỗi 1. Mã ngắn kiểu `demo-100…` trên bảng cũng làm 5 dòng trông giống hệt nhau.
- **Sửa gọn nhất:** đổi mã trong `scripts/demo-seed.sh` sang dạng hex 32 ký tự (giống Olist). Cách này xử lý được cả lỗi 1 và lỗi 3.
- **Ảnh:** `shots/ui-search-demo-id.png`

### Ghi chú nhỏ (không tính là fail)
- Đặt parameter với `effective_at = now` bị từ chối (`effective_at must not be in the past`), vì đến server thì thời điểm đó đã trễ vài mili giây. BRD §8 nói giá trị hiện hành là version có `effective_at <= now`, nhưng thực tế muốn áp dụng ngay thì phải hẹn trễ vài giây.
- `GET /parameters` trả `value` dạng chuỗi (`'5'`), còn `/config` trả số (`5`). Contract chưa ghi điểm này.
- B nhận case A đang giữ thì nhận về `409 INVALID_STATE`, không phải `ALREADY_CLAIMED` (code có mã này nhưng nhánh đó không được dùng tới).
- Ở trang báo "không có quyền" vẫn hiện dòng ghi chú wireframe "Ghi chú: BRD 3.1…".

### Đúng như phần "lỗi đã biết" của BA (đã kiểm, khớp tài liệu)
- #7 Logout trả 204 nhưng token cũ vẫn gọi được `/auth/me` (AU-08).
- #8 Lỗi body request có tiếng Việt, còn lỗi filter queue vẫn tiếng Anh (ER-02, ER-03).
- #2 `status_history` không có DECISION (DE-09).
- FRD §8: `needs_decision=true` mà không kèm status thì ra 0 dòng, vì mặc định là OPEN (DE-02).

## Chi tiết từng ca

### Đăng nhập, hồ sơ, đăng xuất (12/12)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| AU-01 | API §4 /auth/login | Đăng nhập đúng 3 tài khoản | 200 + token + user.role | 200, role=SPECIALIST | Pass |
| AU-02 | API §4 | Sai mật khẩu | 401 | 401 INVALID_CREDENTIALS | Pass |
| AU-03 | API §4 (password 8–256) | Mật khẩu < 8 ký tự | 422 VALIDATION_ERROR | 422 VALIDATION_ERROR | Pass |
| AU-04 | API §1 Bearer | Gọi API không có token | 401 | 401 UNAUTHENTICATED | Pass |
| AU-05 | BRD §3.1, FRD §11 | Đổi ngôn ngữ vi→en được lưu ở user | 200, /auth/me trả en | 200, me=en | Pass |
| AU-06 | BRD §3.1 (vi|en) | Ngôn ngữ ngoài vi/en | 422 | 422 VALIDATION_ERROR | Pass |
| AU-07 | API §3 User | Manager: workload fields có thể null | capacity/slots_left null | capacity=None slots_left=None | Pass |
| AU-10 | FRD §9 | Audit trả items,total,all_total | đủ key | keys=['all_total', 'items', 'total'] | Pass |
| AU-11 | API §8 known quirk | actor_kind có giá trị provenance (QUEUE_SEED…) | ghi nhận như tài liệu | actor_kind gặp: ['USER'] | Pass |
| AU-12 | FRD §9 | Lọc audit theo order | chỉ event của demo-1003 | 200 10 event  | Pass |
| AU-13 | FRD §9 read-only | POST vào audit-events | 405 | 405 | Pass |
| AU-08 | API §1 known issue | Logout rồi dùng lại token cũ | 204; token còn dùng được (lỗi đã biết #7) | logout=204, token cũ gọi /auth/me=200 | Pass |

### Phân quyền theo vai (12/12)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| RG-01 | BRD §2 bảng quyền | Specialist mở Dashboard | 403 | 403 FORBIDDEN | Pass |
| RG-02 | BRD §2 bảng quyền | Specialist mở Audit | 403 | 403 FORBIDDEN | Pass |
| RG-03 | BRD §2 bảng quyền | Specialist xem Parameters | 403 | 403 FORBIDDEN | Pass |
| RG-04 | BRD §2 bảng quyền | Specialist tạo parameter | 403 | 403 FORBIDDEN | Pass |
| RG-05 | BRD §2 bảng quyền | Manager claim case | 403 | 403 FORBIDDEN | Pass |
| RG-06 | BRD §2 bảng quyền | Specialist assign | 403 | 403 FORBIDDEN | Pass |
| RG-07 | BRD §2 bảng quyền | Specialist reopen | 403 | 403 FORBIDDEN | Pass |
| RG-08 | BRD §2 bảng quyền | Specialist ghi Decision | 403 | 403 FORBIDDEN | Pass |
| RG-09 | BRD §2 bảng quyền | Specialist ghi model note | 403 | 403 FORBIDDEN | Pass |
| RG-10 | BRD §2 bảng quyền | Manager ghi Contact Attempt | 403 | 403 FORBIDDEN | Pass |
| RG-11 | API §4 /files Specialist | Manager upload file | 403 | 403 FORBIDDEN | Pass |
| RG-12 | FRD §3 | audit_events: Specialist=null, Manager=list | null / list | spec=NoneType, mgr=list | Pass |

### Risk Queue (18/20)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| QU-01 | FRD §2 acceptance | Response queue có {items,total,limit,offset} | đủ 4 key, limit mặc định 20 | keys=['items', 'limit', 'offset', 'total'] limit=20 | Pass |
| QU-02 | FRD §2 | Mặc định chỉ OPEN (PENDING+IN_PROGRESS) | không có COMPLETED/SKIPPED | status=['IN_PROGRESS', 'PENDING'] | Pass |
| QU-03 | FRD §2 acceptance | Mỗi order chỉ 1 dòng | không trùng order_id | 4 dòng, 4 order | Pass |
| QU-04 | FRD §2 priority | Sort mặc định: score giảm dần | score không tăng | [0.91, 0.82, 0.78, 0.63] | Pass |
| QU-05 | API §3 QueueOrder | Field QueueOrder khớp contract | đúng 22 field | thiếu=[] thừa=[] | Pass |
| QU-06 | UI attempt.html/decision.html vs API §3 | UI đọc contact_count từ list, API list có trả không | có contact_count (UI cần) | API list KHÔNG trả contact_count → UI hiện 'undefined/3' | **FAIL** |
| QU-07 | FRD §2 / API §5 | Filter không hợp lệ: level sai | 422 VALIDATION_ERROR | 422 VALIDATION_ERROR | Pass |
| QU-08 | FRD §2 / API §5 | Filter không hợp lệ: smin > smax | 422 VALIDATION_ERROR | 422 VALIDATION_ERROR | Pass |
| QU-09 | FRD §2 / API §5 | Filter không hợp lệ: limit > 100 | 422 VALIDATION_ERROR | 422 VALIDATION_ERROR | Pass |
| QU-10 | FRD §2 / API §5 | Filter không hợp lệ: sort sai | 422 VALIDATION_ERROR | 422 VALIDATION_ERROR | Pass |
| QU-11 | FRD §2 / API §5 | Filter không hợp lệ: offset âm | 422 VALIDATION_ERROR | 422 VALIDATION_ERROR | Pass |
| QU-12 | FRD §2 / API §5 | Filter không hợp lệ: sla filter sai | 422 VALIDATION_ERROR | 422 VALIDATION_ERROR | Pass |
| QU-13s | API §5 sort | sort=sla | 200 | 200, 4 dòng | Pass |
| QU-13a | API §5 sort | sort=aging | 200 | 200, 4 dòng | Pass |
| QU-14 | API §5 q (hex prefix) | Tìm theo mã đơn demo 'demo-1001' (ô tìm kiếm UI) | tìm được đơn (UI gợi ý tìm theo mã đơn) | 422 VALIDATION_ERROR total=None | **FAIL** |
| QU-15 | API §5 status | Lọc status=COMPLETED | chỉ COMPLETED | ['demo-1004'] | Pass |
| QU-16 | API §5 assignee=me | Lọc đơn của tôi | chỉ đơn assignee = mình | ['demo-1002'] | Pass |
| QU-17 | API §4 summary | Summary có counters, first_pending, me | đủ key | keys=['escalated', 'first_pending', 'high_pending', 'high_pending_overdue', 'me', 'needs_decision', 'overdue', 'stale'] | Pass |
| QU-18 | API §4 filter-options | Filter options có sellers, categories | đủ key | keys=['categories', 'sellers'] | Pass |
| QU-19 | API §1 | Mở order không tồn tại | 404 envelope | 404 ORDER_NOT_FOUND | Pass |

### Nhận case (claim) (4/5)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| CL-01 | BRD §5 | Specialist claim HIGH | bị từ chối | 403 HIGH_RISK_REQUIRES_ASSIGN | Pass |
| CL-02 | BRD §2, §4 | Specialist claim MEDIUM PENDING | 200, IN_PROGRESS, assignee=mình | HTTP 500 ; nhưng DB: status=IN_PROGRESS, assignee=mình | **FAIL** |
| CL-03 | BRD §5 (chống 2 người cùng nhận) | Specialist B claim case A đã nhận | bị từ chối | 409 INVALID_STATE | Pass |
| CL-04 | BRD §2 | Claim case đã COMPLETED | bị từ chối | 409 INVALID_STATE | Pass |
| CL-05 | FRD §4 | active_count/slots_left cập nhật sau claim | active=2, slots=3 | active=2 slots=3 | Pass |

### Comment, model note (6/6)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| CM-01 | BRD §7 | Specialist không giữ case thêm comment | 403 | 403 FORBIDDEN | Pass |
| CM-02 | BRD §7 (1–1000) | Comment rỗng | 422 | 422 VALIDATION_ERROR | Pass |
| CM-03 | BRD §7 (1–1000) | Comment 1001 ký tự | 422 | 422 VALIDATION_ERROR | Pass |
| CM-04 | BRD §7 | Người giữ case thêm comment | 200/201 | 201 | Pass |
| CM-05 | BRD §7 | Manager thêm comment | 200/201 | 201 | Pass |
| CM-06 | BRD §2 | Manager ghi model note | 200/201 | 201 | Pass |

### Upload minh chứng (6/6)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| FI-01 | BRD §6 | Upload PNG hợp lệ | 200/201 + file_id | 201 file_id=có | Pass |
| FI-02 | FRD §6 (magic bytes) | File text đổi đuôi .png | bị từ chối | 422 EVIDENCE_INVALID | Pass |
| FI-03 | BRD §3.5 (≤ 5 MB) | File PDF > 5 MB | bị từ chối | 422 EVIDENCE_INVALID | Pass |
| FI-04 | BRD §3.5 (PNG/JPG/PDF) | File .exe | bị từ chối | 422 EVIDENCE_INVALID | Pass |
| FI-05 | API §4 Owner/Manager | Specialist khác tải file của A | 403/404 | 403 | Pass |
| FI-06 | API §4 Owner/Manager | Manager tải file của A | 200 | 200 | Pass |

### Contact Attempt (9/9)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| CT-01 | BRD §6 | contacted_at ở tương lai | 422 | 422 VALIDATION_ERROR | Pass |
| CT-02 | BRD §6 | contacted_at không có timezone | 422 | 422 VALIDATION_ERROR | Pass |
| CT-03 | BRD §6 | next_contact_date trước ngày liên lạc | 422 | 422 VALIDATION_ERROR | Pass |
| CT-04 | BRD §6 | method sai (FAX) | 422 | 422 VALIDATION_ERROR | Pass |
| CT-05 | BRD §6 | result sai (BUSY) | 422 | 422 VALIDATION_ERROR | Pass |
| CT-06 | BRD §2 | Specialist không giữ case ghi contact | 403 | 403 FORBIDDEN | Pass |
| CT-07 | BRD §6 | Contact hợp lệ kèm 1 evidence | 200/201, contact_count=1 | 201  contact_count=1 | Pass |
| CT-08 | BRD §6 (1 upload dùng 1 lần) | Dùng lại file_id đã gắn | bị từ chối | 422 EVIDENCE_INVALID | Pass |
| CT-09 | BRD §3.5 (tối đa 3 evidence) | Gắn 4 evidence vào 1 contact | bị từ chối | 422 EVIDENCE_INVALID | Pass |

### Complete / Skip (7/7)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| WF-01 | BRD §4 | Complete case đang PENDING | bị từ chối | 409 INVALID_STATE | Pass |
| WF-02 | BRD §4 | Complete với outcome sai | 422 | 422 VALIDATION_ERROR | Pass |
| WF-03 | BRD §4 | Complete HAS_ISSUE | COMPLETED, outcome=HAS_ISSUE | 200 status=COMPLETED | Pass |
| WF-04 | FRD §8 | Case vừa đóng có needs_decision và closed_at | needs_decision=true, closed_at có | needs_decision=True closed_at=có | Pass |
| WF-05 | BRD §4 | Skip OTHER không có note | bị từ chối | 422 VALIDATION_ERROR | Pass |
| WF-06 | BRD §4 | Skip reason sai | 422 | 422 VALIDATION_ERROR | Pass |
| WF-07 | BRD §4 | Skip OTHER có note | SKIPPED, skip_reason=OTHER | 200 status=SKIPPED reason=OTHER | Pass |

### Reopen (5/5)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| RO-01 | BRD §4 | Manager reopen case COMPLETED | PENDING, cycle+1, không assignee, giữ original_queued_at | 200 status=PENDING cycle 1→2 assignee=None | Pass |
| RO-02 | BRD §8 (SLA ghi khi reopen) | SLA cycle mới = sla_hours theo mức | 24 giờ | 24.0 giờ (MEDIUM) | Pass |
| RO-03 | BRD §4 (giữ lịch sử cũ) | Lịch sử cycle cũ còn sau reopen | cycles ≥ 2, contacts cũ còn | cycles=2 contacts=1 | Pass |
| RO-04 | BRD §4 | Reopen case đang PENDING | bị từ chối | 409 INVALID_STATE | Pass |
| RO-05 | BRD §4 (reopen_review_times=2) | Reopen khi reopen_count=2 ≥ 2 mà không review_confirmed | bị từ chối, có confirm thì qua | không confirm=422 REVIEW_CONFIRMATION_REQUIRED; confirm=200; (lần 1=200, lần 2=200) | Pass |

### Parameter Settings (12/12)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| PA-01 | BRD §8, FRD §10 | Danh sách parameter | đúng 14 key | 14 key, thiếu=[] | Pass |
| PA-02 | BRD §8 | Parameter không hợp lệ: capacity_warn = capacity (5) | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-03 | BRD §8 | Parameter không hợp lệ: hours = 721 | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-04 | BRD §8 | Parameter không hợp lệ: hours = 0 | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-05 | BRD §8 | Parameter không hợp lệ: days = 61 | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-06 | BRD §8 | Parameter không hợp lệ: orders = 21 | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-07 | BRD §8 | Parameter không hợp lệ: times = 11 | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-08 | BRD §8 | Parameter không hợp lệ: sla_calendar sai enum | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-09 | BRD §8 | Parameter không hợp lệ: key không tồn tại | bị từ chối | 422 PARAMETER_INVALID | Pass |
| PA-10 | BRD §8 (cần reason) | Tạo version không có reason | bị từ chối | 422 VALIDATION_ERROR | Pass |
| PA-11 | BRD §8 (effective tương lai) | Version hẹn ngày tương lai | nằm ở scheduled, current vẫn 2 | 201 current=2 scheduled=1 | Pass |
| PA-12 | API §6 | /config đúng danh sách key, không có typical_order | khớp | thiếu=[] thừa=[] | Pass |

### Giao case, capacity (11/11)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| AS-00 | BRD §8 (version mới hiệu lực ngay) | Hạ capacity=2, capacity_warn=1 | /config trả 2 và 1 | 201,201 capacity=2 warn=1 | Pass |
| AS-01 | BRD §5 | Manager giao HIGH cho B | IN_PROGRESS, assignee=B | 200 status=IN_PROGRESS | Pass |
| AS-02 | BRD §5 | Giao case thứ 2 cho B (vừa đủ capacity) | 200 | 200  | Pass |
| AS-03 | BRD §5 | Giao vượt capacity không override | bị từ chối | 422 CAPACITY_FULL | Pass |
| AS-04 | BRD §5 | Override capacity không có reason | bị từ chối | 422 REASON_REQUIRED | Pass |
| AS-05 | BRD §5 | Override capacity có reason | 200 | 200  | Pass |
| AS-06 | BRD §5, FRD §4 | Reassign không có reason | bị từ chối | 422 REASON_REQUIRED | Pass |
| AS-07 | BRD §5 | Reassign có reason | assignee=A | 200  | Pass |
| AS-08 | FRD §4 (Specialist ID) | Giao case cho Manager | bị từ chối | 422 VALIDATION_ERROR | Pass |
| AS-09 | FRD §4 | Workload B sau giao/giao lại | active=2 (1001,1005) | active=2 slots=0 | Pass |
| AS-10 | BRD §5 (audit override) | Audit có sự kiện override capacity | ≥ 1 event, lọc override-only chạy | 200 3 event | Pass |

### Giới hạn số lần liên lạc (2/2)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| MC-01 | BRD §3.6, §6 | Lần thứ 3 không REACHED | case tự SKIPPED/UNREACHABLE | 201 status=SKIPPED reason=UNREACHABLE count=3 | Pass |
| MC-02 | BRD §6 (không vượt max_contact) | Liên lạc lần 4 | bị từ chối | 409 INVALID_STATE | Pass |

### Manager Decision (9/9)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| DE-01 | FRD §8 | Danh sách cần quyết định (COMPLETED+SKIPPED) | có demo-1001 | ['demo-1001', 'demo-1002', 'demo-1004'] | Pass |
| DE-02 | FRD §8 (ghi chú: default OPEN) | needs_decision=true không kèm status | 0 dòng (vì mặc định OPEN) — đúng như FRD ghi | total=0 | Pass |
| DE-03 | BRD §7 | Decision thiếu reason | bị từ chối | 422 REASON_REQUIRED | Pass |
| DE-04 | BRD §7 | Decision thiếu next_step | bị từ chối | 422 VALIDATION_ERROR | Pass |
| DE-05 | BRD §7 | Decision due_date ở quá khứ | bị từ chối | 422 VALIDATION_ERROR | Pass |
| DE-06 | BRD §7 | Decision code sai | 422 | 422 VALIDATION_ERROR | Pass |
| DE-07 | FRD §8 | Decision hợp lệ → thành next_step | next_step = decision mới | 201 next_step=có | Pass |
| DE-08 | BRD §7 (append-only) | Decision thứ 2 không ghi đè decision cũ | decisions = 2, next_step = mới nhất | decisions=2 | Pass |
| DE-09 | API §8 known quirk | status_history không gồm DECISION (lỗi đã biết) | không có DECISION — khớp tài liệu | không có DECISION | Pass |

### Dashboard (8/8)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| DB-01 | FRD §7 | Dashboard days=1 | 200 | 200 | Pass |
| DB-03 | FRD §7 | Dashboard days=3 | 200 | 200 | Pass |
| DB-07 | FRD §7 | Dashboard days=7 | 200 | 200 | Pass |
| DB-04 | FRD §7 (days=1|3|7) | Dashboard days=5 | 422 | 422 VALIDATION_ERROR | Pass |
| DB-05 | API §7 | Dashboard order view đủ block | đủ 15 key | thiếu=[] | Pass |
| DB-06 | API §7 totals | totals đủ 10 counter | đủ | thiếu=[] | Pass |
| DB-07 | API §7 | Dashboard view=product có block product | product.{totals,by_category,top_items} | 200 product keys=['by_category', 'top_items', 'totals'] | Pass |
| DB-08 | Đối chiếu số | totals.open = số dòng queue OPEN | bằng nhau | dashboard=3 queue=3 | Pass |

### Lỗi và ngôn ngữ (3/3)

| Ca | Mục BA | Kiểm gì | Mong đợi | Thực tế | KQ |
|---|---|---|---|---|---|
| ER-01 | API §1, FRD §11 | Envelope lỗi {error:{code,message,details}} | đủ 3 key | keys=['code', 'details', 'message'] | Pass |
| ER-02 | FRD §11 (validation vi/en) | Message lỗi body request theo Accept-Language | vi ≠ en | vi='Dữ liệu không hợp lệ' / en='Validation error' | Pass |
| ER-03 | BA lỗi đã biết #8 | Lỗi filter queue (VALIDATION_ERROR) khi Accept-Language=vi | vẫn tiếng Anh — khớp lỗi đã biết | message='level must be HIGH, MEDIUM, or LOW' | Pass |

## Chưa test được

- (Dữ liệu Olist thật và case mức LOW: đã test ở vòng 2 bên dưới.)
- Job `recalculate-sla` và SLA `BUSINESS_HOURS`: BA đã ghi là chưa hoạt động.
- Tranh nhận cùng lúc thật sự (2 request song song): mới test tuần tự.

Script test: `tools/ba_test.py` (chạy lại được sau `make demo-seed`).

---

# Vòng 2 — test lại với dữ liệu Olist thật (03/11/2026)

## Đã làm
1. Chép 9 file CSV Olist (bản trong Thùng rác `archive1`) vào `data/raw/olist`.
2. Chạy đường dữ liệu của repo: `make bronze-manifest` rồi `make ingest` (run id `fcb93adf-…`, khoảng 11 giây), sau đó dbt build.
3. Repo có sẵn adapter `infrastructure/postgres_queue_seeding.py` (`QueueSeeder`) nhưng **không có lệnh CLI hay Makefile nào gọi nó**, và cũng không có bước tạo prediction cho 100 đơn Olist như `BA/README.md` mô tả, nên mình không tái tạo được đúng môi trường BA đã đối chiếu. Mình tự nạp 100 đơn thật từ `gold.ml_modelling_items` vào app (109 sản phẩm: 27 HIGH, 38 MEDIUM, 35 LOW) bằng `tools/olist_ui_seed.sql`. Script theo đúng khuôn `demo-seed.sh`. Score là số giả cố định (deterministic), **không phải model chấm**, đúng như BA mô tả.
4. Chạy lại toàn bộ ca test với mã đơn thật (H1=06daa9224cad114ece451ff00c20d49f H2=0f1e7409f75f39dd6de647d802dd1094 M1=0ab82628350881eff00a09a3a0c73970 M2=0d6350e1fa2acb1318e3a53d52333e25 L1=0d2676e37c740455a4f662cb7a88e6f1).

## Kết quả
| Bộ kiểm | Kết quả |
|---|---|
| dbt build trên Olist thật (38 model, 82 data test, 2 unit test) | **122/122 PASS** (sau khi vượt 2 lỗi bên dưới) |
| Ca test theo BA, mã đơn thật | **127/128 pass** |

- **Lỗi 1 (nhận case bị 500) và lỗi 3 (không tìm được mã) KHÔNG còn** khi dùng mã Olist thật. Vậy 2 lỗi này chỉ do mã demo `demo-100x` trong `demo-seed.sh`.
- Tìm theo 8 ký tự đầu mã đơn và theo Product Item ID (`<mã>-1`) đều chạy, trả đúng `matched_item_id`.
- Specialist nhận được case LOW và hoàn tất bình thường (vòng 1 không test được vì demo không có LOW).
- **Lỗi 2 (`contact_count` → `undefined/3`) vẫn còn.**

## Lỗi mới tìm được ở vòng này

### 4. `make warehouse` chạy là hỏng, không in ra lỗi gì
- Image `infra/jobs/Dockerfile` chạy bằng `USER 10001`, nhưng `/workspace/dbt` thuộc root. dbt không ghi được `logs/` và `target/` nên thoát với mã 2 mà không có dòng log nào.
- Cách vượt khi test: `-e DBT_LOG_PATH=/tmp/l -e DBT_TARGET_PATH=/tmp/t`.
- Sửa: `chown` thư mục cho user 10001 trong Dockerfile, hoặc đặt sẵn 2 biến môi trường trên.

### 5. `make warehouse` không truyền `source_run_id`
- Mọi model silver gọi macro `validated_source_run_id`, nên bắt buộc có `--vars source_run_id=<uuid>`. Target `warehouse` trong Makefile không truyền biến này, vì vậy làm theo README thì chắc chắn fail (9 lỗi compile, 114 SKIP).
- Sửa: cho Makefile nhận `SOURCE_RUN_ID` (giống target `p4-release-verify`), và README nói rõ lấy run id từ output của `make ingest`.

### 6. Chấm điểm lại thì case đang xử lý bị kẹt vĩnh viễn và giữ luôn slot của nhân viên (thiết kế)
- Khi kích hoạt một prediction mới (prediction cũ chuyển `SUPERSEDED`), các case cũ biến mất khỏi queue và API trả `404 ORDER_NOT_FOUND`.
- Nhưng case `IN_PROGRESS` vẫn được tính vào `active_count`: nhân viên A còn 2/5 slot bị chiếm bởi 2 case không ai nhìn thấy.
- Không đóng được các case này, kể cả bằng SQL: trigger `p7_case_guard` báo `prediction must be ACTIVE`. Muốn gỡ phải tắt trigger.
- Đường chính thức cũng dính: `PostgresQueueSeedStore.seed()` dùng `INSERT … ON CONFLICT (order_id) DO NOTHING`, nên nếu chấm lại mà đơn đã có case từ prediction cũ, đơn đó bị bỏ qua và tiếp tục ẩn khỏi queue. Trong repo không có bước nào chuyển hay đóng case cũ khi đổi prediction.
- BRD §9 có ghi "chỉ một prediction ACTIVE" và "case giữ prediction_id lúc tạo", nhưng chưa nói chấm lại thì case cũ xử lý thế nào. Cần BA/BE chốt: hoặc chuyển case sang prediction mới, hoặc tự đóng, hoặc không tính vào capacity.

## Môi trường test — để người đọc biết số liệu đến từ đâu
- Số ca pass/fail là của script test mình tự viết theo BA (`tools/ba_test.py`), không phải bộ test chính thức của repo.
- Mình có can thiệp vào DB local: tạo thêm Specialist `test_specialist_b`; tự nạp 100 đơn (khác `QueueSeeder` ở chỗ thời gian vào queue rải trong 3 ngày và không ghi audit `QUEUE_SEED`); tắt trigger `p7_case_guard` một lần để đóng 2 case demo bị kẹt (lỗi 6).
- Lỗi 4 đã kiểm trực tiếp: trong container, `touch /workspace/dbt/x` báo `Permission denied`; `dbt parse` thoát mã 2 với 0 byte output.

## Ghi chú giao diện với dữ liệu thật
- Mã đơn hiện 8 ký tự đầu, các dòng phân biệt được rõ. Chi tiết đơn hiện đậm 8 ký tự đầu, phần còn lại nhạt, đúng thiết kế.
- Ngành hàng chỉ dịch một phần: "Sức khỏe & làm đẹp", "Nội thất văn phòng" có tiếng Việt, nhưng "Stationery", "Electronics", "Auto", "Baby", "Audio" vẫn tiếng Anh.
- Ô "Khách hàng" và "Giá trị đơn" ở Chi tiết đơn để trống. Đúng lỗi đã biết #9 (DTO không trả thông tin thương mại), nhưng giao diện vẫn hiện nhãn với ô trống; nên ẩn đi hoặc ghi "Chưa có dữ liệu".
- Tỉ lệ quá hạn SLA cao (63/98) là do script nạp của mình đặt thời gian vào queue rải trong 3 ngày, còn SLA HIGH chỉ 4 giờ. Không phải lỗi.
- Ảnh: `shots_olist/`


---

# Vòng 3 — bấm tay trên giao diện theo FRD (Trúc test, 03/11/2026)

Dữ liệu: 100 đơn Olist thật của vòng 2. Trúc đăng nhập 3 tài khoản và bấm thật trên từng màn.

## Lỗi mới

### 7. Giao diện không lưu được lần liên lạc nào, Manager không đổi được tham số nào (nặng)
- **Làm:** màn Liên lạc khách, chọn thời điểm 02/11 15:39 (đã qua), bấm "Lưu lần liên lạc". Màn Cài đặt, đổi `capacity_warn`, hiệu lực 03/11 12:45 (bây giờ).
- **Thực tế:** bị chặn với câu `contacted_at must not be in the future` và `effective_at must not be in the past`. Chọn giờ nào cũng bị.
- **Nguyên nhân:** `frontend/prototype/js/common.js:184` (`apiTime`) gửi thời gian dạng `2026-11-02 15:39`, **không kèm múi giờ**. Backend bắt buộc có múi giờ (BRD §6) nên từ chối. Câu báo lỗi còn sai lý do, vì `domain/workflow.py:76–77` gộp "thiếu múi giờ" và "ở tương lai" vào một câu.
- Kiểm bằng API: gửi `effective_at: "2026-11-10 10:00"` (tương lai, không múi giờ) vẫn bị `must not be in the past`.
- **Bị ảnh hưởng:** `attempt.html:229` (ghi liên lạc) và `settings.html:98` (đổi tham số). Kéo theo trên UI không test được: đính kèm minh chứng, tự chuyển SKIPPED/UNREACHABLE sau lần cuối, quy tắc `capacity_warn < capacity`.
- **Sửa:** `apiTime` gửi ISO kèm múi giờ (ví dụ `new Date(v).toISOString()`); backend tách thông báo lỗi khi thiếu múi giờ.
- **Vì sao vòng 1–2 không bắt được:** script gọi thẳng API với thời gian có múi giờ. Ca CT-02 có test "không múi giờ → 422" và chấm đúng, vì backend làm đúng BRD; chỗ sai là định dạng giao diện gửi lên.
- **Ảnh:** `shots_ui/attempt-loi7.png`, `shots_ui/settings-loi7.png`

### 8. Ghi quyết định mà để trống ô "Hạn" thì bị 422
- **Làm:** Manager, màn Quyết định, chọn quyết định, điền Lý do + Bước tiếp theo, **để trống Hạn**, bấm Lưu.
- **Thực tế:** `POST /decisions` trả 422, UI hiện "Dữ liệu không hợp lệ". Điền ngày vào ô Hạn thì lưu được.
- **Nguyên nhân:** `decision.html:148` gửi `due_date: el("dc-due").value`, ô trống thành chuỗi `""`; API chỉ nhận ngày hoặc `null`. Kiểm bằng API: `due_date: ""` → 422, `due_date: null` → 201.
- **Sửa:** `due_date: el("dc-due").value || null`.

## Kiểm lại toàn bộ thao tác bằng script bấm giao diện (Playwright, 20 bước)
Script `tools/ui_all.py` đăng nhập thật, bấm thật trên giao diện và ghi lại API mà mỗi thao tác gọi. Lỗi 7 kiểm riêng bằng `tools/verify7.py`: giao diện gửi `"contacted_at":"2026-11-03 12:51"` và `"effective_at":"2026-11-20 10:00"` (không múi giờ), cả hai bị 422.

| Bước | Mong đợi | API giao diện đã gọi | KQ | Ghi chú |
|---|---|---|---|---|
| UI-01 Queue: lọc Mức = HIGH | GET level=HIGH 200, bảng chỉ còn HIGH | GET /orders?level=HIGH&status=OPEN&limit=8&offset=0 → 200 | Pass |  |
| UI-02 Queue: sắp xếp theo SLA | GET sort=sla 200 | GET /orders?level=HIGH&status=OPEN&sort=sla&limit=8&offset=0 → 200 | Pass |  |
| UI-03 Queue: Tải thêm | GET offset>0 200 | GET /orders?status=OPEN&sort=sla&limit=8&offset=0 → 200; GET /orders?status=OPEN&sort=sla&limit=16&offset=0 → 200 | Pass | Giao diện tải lại với limit lớn hơn (8 → 16) thay vì dùng offset; chạy đúng, script ban đầu kỳ vọng sai |
| UI-04 Queue: lọc theo seller (Lọc thêm) | GET seller=… 200 | GET /orders?status=OPEN&seller=04308b1ee57b6625f47df1d56f00eedf&sort=sla&l → 200 | Pass |  |
| UI-05 Nhận đơn MEDIUM/LOW | POST claim 200 | POST /orders/e3194d56283622975638628a739c9e84/claim → 200; GET /orders?status=OPEN&limit=8&offset=0 → 200 | Pass |  |
| UI-06 Thêm nhận xét | POST comments 201 | POST /orders/f65b97e0ce63435e9d58afec633f3f69/comments → 201 | Pass |  |
| UI-07 Bỏ qua 'Khác' trống ghi chú | bị chặn (không gọi API hoặc 4xx) | POST /orders/f65b97e0ce63435e9d58afec633f3f69/skip → 422 — A note is required for OTHER | Pass |  |
| UI-08 Hoàn tất đơn | POST complete 200 | POST /orders/f65b97e0ce63435e9d58afec633f3f69/complete → 200 | Pass |  |
| UI-09 Hồ sơ: đổi sang EN | PATCH /auth/me 200 | PATCH /auth/me → 200 | Pass |  |
| UI-10 Giao đơn HIGH cho A | POST assign 200 | POST /orders/1cfce7466cb5b7c473426907c2cb148f/assign → 200 | Pass |  |
| UI-11 Chuyển người, trống lý do | bị chặn | (không gọi API) — Nhập lý do: chuyển người và vượt capacity đều được ghi vào lịch sử. | Pass |  |
| UI-12 Chuyển người có lý do | POST assign 200 | POST /orders/1cfce7466cb5b7c473426907c2cb148f/assign → 200 | Pass |  |
| UI-13 Ghi quyết định | POST decisions 201 | POST /orders/f65b97e0ce63435e9d58afec633f3f69/decisions → 422 — Dữ liệu không hợp lệ | **FAIL** | Lỗi 8 |
| UI-14 Danh sách Quyết định không còn 'undefined' | không có chữ undefined | (không gọi API) — Dữ liệu không hợp lệ | **FAIL** | Lỗi 2 |
| UI-15 Mở lại đơn đã đóng | POST reopen 200 | POST /orders/f65b97e0ce63435e9d58afec633f3f69/reopen → 200 | Pass |  |
| UI-16 Tổng quan: lọc Mức = HIGH | GET dashboard level=HIGH 200 | GET /dashboard?level=HIGH&view=order → 200; GET /orders?level=HIGH&status=PENDING&limit=4 → 200 | Pass |  |
| UI-17 Tổng quan: Theo sản phẩm | GET dashboard view=product 200 | GET /orders?level=HIGH&status=PENDING&limit=4 → 200; GET /dashboard?level=HIGH&view=product → 200 | Pass |  |
| UI-18 Lịch sử: lọc loại sự kiện | GET event_type=… 200 | GET /audit-events?event_type=CLAIM → 200 | Pass |  |
| UI-19 Lịch sử: chỉ override | GET override_only=true 200 | GET /audit-events?event_type=CLAIM&override_only=true → 200 | Pass |  |
| UI-20 Lịch sử: lọc người làm | GET actor_id=… 200 | GET /audit-events?event_type=CLAIM&actor_id=86673bfb-5dee-4346-9f4a-d14459 → 200 | Pass |  |

Kết quả: 18/20 bước đúng; 2 bước fail ứng với lỗi 2 và lỗi 8.

## Xác nhận thêm trên giao diện
- Lỗi 2 (`undefined/3`) hiện ở danh sách "Đơn được giao cho tôi" (`shots_ui/attempt-loi7.png`).
- Thông báo lỗi tiếng Anh nằm giữa giao diện tiếng Việt, khớp lỗi đã biết #8.

## Chạy đúng trên giao diện
- Lọc, sắp xếp, tải thêm ở Risk Queue; nhận đơn MEDIUM/LOW; ô "Đang giữ" cập nhật.
- Nhận xét; Hoàn tất / Bỏ qua (Bỏ qua "Khác" mà trống ghi chú thì bị chặn); đổi VI/EN.
- Manager giao đơn HIGH, giao lại (trống lý do thì bị chặn); ghi quyết định; mở lại đơn: lịch sử trạng thái hiện đủ Nhận đơn → Bỏ qua (Trùng case) → Mở lại → Chu kỳ 2 (`shots_ui/order-reopen.png`).
- Tổng quan (bộ lọc, Theo đơn / Theo sản phẩm), Lịch sử thao tác (lọc).
- Bảng "Lịch sử thay đổi" ở Cài đặt hiện đúng cũ → mới, phiên bản, trạng thái (Đang hiệu lực / Đã thay / Đã lên lịch).

## Ghi chú nhỏ
- Ô "Bộ tham số áp dụng" ở Chi tiết đơn luôn trống.
- "Dòng thời gian đơn" chỉ có "Vào Risk Queue"; ô Khách hàng, Giá trị đơn trống (lỗi đã biết #9).

## Còn chưa test
- Đính kèm JPG/PDF trên UI, tự chuyển Bỏ qua, quy tắc `capacity_warn < capacity` trên UI: bị lỗi 7 chặn (đã test bằng API ở vòng 1–2).
- Tranh nhận cùng lúc, job `recalculate-sla`, model chấm điểm thật.

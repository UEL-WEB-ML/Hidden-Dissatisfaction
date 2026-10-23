# BẢNG MÔ TẢ DỮ LIỆU PHẦN WEB (DATA DICTIONARY)

## Hệ thống hỗ trợ chăm sóc khách hàng cho đơn hàng và sản phẩm có nguy cơ bất mãn ẩn

| Thuộc tính | Nội dung |
|---|---|
| Phiên bản | 0.5 |
| Trạng thái | Bản nháp, chờ duyệt: khớp ERD, kiểu dữ liệu PostgreSQL (khoá chính/khoá ngoại), phần view đọc từ ML |
| Ngày | 21/10/2026 |
| Nguồn | Tab DATA DICTIONARY WEB trong sheet phân công của nhóm. Sửa ở đây hoặc ở sheet thì cập nhật cả hai cho khớp |
| Tài liệu liên quan | BRD v4.2; FRD v2.2; API_CONTRACT_olist_hidden_dissatisfaction.md v0.5; ERD – TBD |

### Thay đổi so với v0.2 (13/10)

| Bảng | Thay đổi | Lý do |
|---|---|---|
| `app.contact_evidence` | `contact_id` cho phép NULL; `evidence_id` dùng làm `file_id` của API | API contract v0.3: upload tệp (`POST /files`) trước rồi mới ghi lần liên lạc |

### Thay đổi so với v0.1 (05/10)

| Bảng | Thay đổi | Lý do |
|---|---|---|
| `app.users` | Thêm `preferred_language` | FRD F11-S01 |
| `app.review_cases` | Thêm `cycle_no`, `original_queued_at`, `aggregation_rule`; bỏ `sla_due_at` (chuyển sang `review_cycles`) | BRD 6.1, 6.8 |
| `app.review_cycles` | **Bảng mới**: mỗi lần vào queue / mở lại là một chu kỳ | BRD 6.8, FRD 4.1 Review Cycle |
| `app.contact_attempts` | Gắn với `cycle_id`; bỏ `CHECK 1–3` cố định; thêm `evidence_ref` | BRD 6.8 (reset bộ đếm), feedback 13/10 |
| `app.contact_evidence` | **Bảng mới**: tệp minh chứng liên lạc | BRD 6.6/6.11; FRD F07-S03 |
| `app.case_comments` | **Bảng mới**: nhận xét của nhân viên/quản lý | BRD 6.11; FRD F08-S05 |
| `app.manager_decisions` | **Bảng mới**: quyết định + bước tiếp theo | BRD 6.12; FRD F12 |
| `app.audit_events` | `case_id` cho phép NULL; thêm 3 loại event | FRD F09-S02, BRD 6.9 |
| `app.config` | **Thay bằng** `app.parameter_definitions` + `app.parameters` (mỗi dòng là một phiên bản của một tham số) | BRD 6.9, FRD F10 |
| `ml.v_risk_items_for_web` | **View mới** ở cấp sản phẩm | BRD 6.1 mục 2, FRD F04-S03 |
| `ml.v_risk_orders_for_web` | Thêm `aggregation_rule`, `items_count`; score là điểm tổng hợp | BRD 6.1 mục 3 |

## 1. Phạm vi

- **Schema `app`**: các bảng của web (tài khoản, case, chu kỳ, phân công, liên lạc, minh chứng, nhận xét, quyết định, audit, tham số). Web được đọc và ghi.
- **View `ml.v_risk_orders_for_web`, `ml.v_risk_items_for_web`**: kết quả dự đoán (cấp đơn và cấp sản phẩm) và bối cảnh đơn do bên ML/Data Warehouse cung cấp. Web chỉ đọc, không bao giờ sửa risk score.
- Dữ liệu Olist gốc (bronze/silver/gold) nằm ở bản mô tả bên ML, không lặp lại ở đây.

Tên cột và các mã (`SPECIALIST`, `PHONE`, `CONTACT`…) trong tài liệu này cũng là tên field và mã dùng trong API contract.

## 2. Điểm cần nhóm xem

1. **Ngưỡng HIGH/MEDIUM thuộc release ML**, không thuộc `app.parameters`. Pipeline chọn ngưỡng trên validation theo policy đã khai báo, lưu trong `ml.model_thresholds`, và API đọc theo cặp định danh `(release_version, threshold_version)`. Các giá trị 0,70/0,45 trong mock data chỉ là ví dụ của `thr-v1`, không phải hằng số nghiệp vụ.
2. **Quy tắc tổng hợp `aggregation_rule`**: đã chốt `max-v1` (điểm đơn = điểm product item cao nhất). Mọi thay đổi công thức phải dùng version mới.
3. **`synthetic_data_flag`**: nhóm ML chốt sản phẩm nào được giả lập, sinh bằng cách nào; web chỉ đọc cờ và gắn nhãn.
4. **`close_note`** dùng cho cả hoàn tất và bỏ qua, không bắt buộc, trừ `skip_reason = 'OTHER'`.
5. **Đăng nhập bằng session hay JWT**: nếu chọn session lưu ở database thì cần thêm bảng `app.sessions`.
6. **Múi giờ**: cột lưu `timestamptz`, ví dụ đang ghi `+07`, nhưng dữ liệu Olist là giờ Brazil (`-03`). Cần chốt hiển thị theo giờ nào (điểm 1 ở mục 7 của API contract).
7. **Kho tệp minh chứng**: `contact_evidence.storage_key` trỏ tới đâu (thư mục trên server, object storage), giữ bao lâu, ai xem được.
8. **Danh mục quyết định và retention policy**: các bảng đã có BRD/FRD; Product Owner vẫn cần duyệt danh mục decision và thời hạn lưu tệp.

## 3. Các bảng

### `app.users`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `user_id` | uuid | Có | PK, mặc định gen_random_uuid() | Mã người dùng | 5f0c2b9e-… | FRD 4.1 User/Role; BRD 3 |
| `username` | varchar(50) | Có | UNIQUE | Tên đăng nhập, tài khoản tạo sẵn (không có đăng ký) | nhanvien | FRD 4.1 User/Role; BRD 3 |
| `password_hash` | text | Có |  | Mật khẩu đã băm (bcrypt/argon2), không lưu mật khẩu thô | $2b$12$… | FRD 4.1 User/Role; BRD 3 |
| `full_name` | varchar(100) | Có |  | Họ tên hiện trên giao diện | Trần Thị B | FRD 4.1 User/Role; BRD 3 |
| `role` | varchar(20) | Có | CHECK IN ('SPECIALIST','MANAGER') | Vai, quyết định màn và quyền thao tác | SPECIALIST | FRD 4.1 User/Role; BRD 3 |
| `preferred_language` | varchar(2) | Không | CHECK IN ('vi','en'); NULL = chưa lưu | Ngôn ngữ giao diện lưu theo tài khoản | vi | FRD F11-S01 |
| `is_active` | boolean | Có | Mặc định true | Tắt tài khoản thay vì xoá (giữ lịch sử audit) | true | FRD 4.1 User/Role; BRD 3 |
| `created_at` | timestamptz | Có | Mặc định now() | Thời điểm tạo tài khoản | 2018-05-01 08:00:00+07 | FRD 4.1 User/Role; BRD 3 |

### `app.review_cases`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `case_id` | uuid | Có | PK | Mã case xử lý | 9a1e… | FRD 4.1 Order Risk Case |
| `order_id` | varchar(32) | Có | FK → đơn hàng Olist (gold); UNIQUE | Mã đơn Olist (một đơn một case; mở lại thì thêm chu kỳ, không thêm case) | a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30 | FRD 4.1 Order Risk Case |
| `prediction_id` | uuid | Có | FK → ml.predictions | Lần dự đoán đưa đơn vào queue (giữ đúng score/model lúc đó) | c2d4… | BRD 6.1 |
| `aggregation_rule` | varchar(20) | Có |  | Quy tắc tổng hợp điểm sản phẩm thành điểm đơn, có version | max-v1 | BRD 6.1 mục 3–4 |
| `status` | varchar(20) | Có | CHECK IN ('PENDING','IN_PROGRESS','COMPLETED','SKIPPED'); mặc định 'PENDING' | Trạng thái xử lý | IN_PROGRESS | BRD 6.4 |
| `assignee_id` | uuid | Không | FK → app.users; NULL khi PENDING | Người đang phụ trách | 5f0c2b9e-… | BRD 6.3 |
| `cycle_no` | smallint | Có | Mặc định 1; = số chu kỳ hiện tại trong `review_cycles` | Chu kỳ xử lý hiện tại | 2 | BRD 6.8 |
| `original_queued_at` | timestamptz | Có | Không đổi sau khi tạo | Lần vào Risk Queue đầu tiên (tính total aging, biểu đồ xu hướng) | 2018-05-25 09:00:00+07 | BRD 6.7, 6.8; F01-S08 |
| `outcome` | varchar(30) | Khi COMPLETED | CHECK IN ('HAS_ISSUE','NO_ISSUE','DUPLICATE') | Kết quả khi hoàn tất; `UNREACHABLE` không hợp lệ ở đây | NO_ISSUE | BRD 6.5 |
| `skip_reason` | varchar(30) | Khi SKIPPED | CHECK IN ('UNREACHABLE','DUPLICATE','REFUSED','NOT_APPLICABLE','OTHER') | Lý do bỏ qua (danh mục chờ PO duyệt) | UNREACHABLE | BRD 6.6 |
| `close_note` | text | Khi skip_reason='OTHER' |  | Ghi chú khi đóng case | Khách đã đổi số điện thoại | BRD 6.6 |
| `closed_at` | timestamptz | Khi đã đóng |  | Lúc hoàn tất hoặc bỏ qua | 2018-06-04 16:10:00+07 | BRD 6.4 |
| `reopen_count` | smallint | Có | Mặc định 0 | Số lần Manager mở lại | 1 | BRD 6.7 |
| `updated_at` | timestamptz | Có | Mặc định now(), cập nhật mỗi thao tác | Lần cập nhật gần nhất (tính "quá lâu không cập nhật") | 2018-06-04 11:30:00+07 | BRD 6.7 |
| `row_version` | integer | Có | Mặc định 0, tăng mỗi lần sửa | Khoá lạc quan: 2 người cùng claim thì chỉ người đầu tiên thành công (409 cho người sau) | 3 | BRD 6.3 mục 8 |

### `app.review_cycles` (mới)

Mỗi lần case vào queue hoặc được mở lại là một chu kỳ. SLA và bộ đếm liên lạc tính trong chu kỳ (BRD 6.8: mở lại thì reset retry counter và SLA).

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `cycle_id` | uuid | Có | PK | Mã chu kỳ | 3b7c… | FRD 4.1 Review Cycle |
| `case_id` | uuid | Có | FK → app.review_cases | Case | 9a1e… | FRD 4.1 Review Cycle |
| `cycle_no` | smallint | Có | UNIQUE (case_id, cycle_no) | Thứ tự chu kỳ | 2 | BRD 6.8 |
| `started_at` | timestamptz | Có |  | Lúc vào queue (chu kỳ 1) hoặc lúc mở lại; mốc tính SLA | 2018-06-02 09:00:00+07 | BRD 6.7 |
| `ended_at` | timestamptz | Không | NULL = chu kỳ đang chạy | Lúc case COMPLETED/SKIPPED trong chu kỳ này | 2018-06-02 16:00:00+07 | BRD 6.7 |
| `reopen_reason` | text | Khi cycle_no > 1 |  | Lý do mở lại | Khách gửi thêm khiếu nại | BRD 6.8 |
| `reopened_by` | uuid | Khi cycle_no > 1 | FK → app.users (role MANAGER) | Manager mở lại | 8b2a… | BRD 6.8 |
| `sla_due_at` | timestamptz | Có | Tính từ `started_at` + SLA theo mức rủi ro của bộ tham số đang hiệu lực; tính lại khi tham số đổi (case đang mở) | Hạn SLA của chu kỳ | 2018-06-02 13:00:00+07 | BRD 6.7, 6.9 |
| `parameter_version` | varchar(30) | Khi đã đóng | Ghi lúc chu kỳ kết thúc | Bộ tham số áp dụng khi đóng (case đã đóng giữ lịch sử) | ps-20180521-0800 | BRD 6.9 mục 3 |

### `app.assignments`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `assignment_id` | uuid | Có | PK | Mã lần phân công | e71b… | FRD 4.1 Review Assignment |
| `case_id` | uuid | Có | FK → app.review_cases | Case được phân công | 9a1e… | BRD 6.3 |
| `cycle_id` | uuid | Có | FK → app.review_cycles | Chu kỳ | 3b7c… | BRD 6.8 |
| `assignee_id` | uuid | Có | FK → app.users (role SPECIALIST) | Người nhận | 5f0c2b9e-… | BRD 6.3 |
| `assigned_by` | uuid | Có | FK → app.users | Người thực hiện (chính Specialist khi CLAIM, Manager khi ASSIGN/REASSIGN) | 8b2a… | BRD 6.3 |
| `method` | varchar(20) | Có | CHECK IN ('CLAIM','ASSIGN','REASSIGN'); CLAIM chỉ khi risk level ≠ HIGH (backend kiểm) | Cách nhận đơn | CLAIM | BRD 6.3 mục 1 |
| `override_capacity` | boolean | Có | Mặc định false | Manager giao vượt capacity | false | BRD 6.3 mục 9 |
| `reason` | text | Khi REASSIGN hoặc override |  | Lý do chuyển người / vượt capacity | B nghỉ chiều nay | BRD 6.3, 6.8 |
| `started_at` | timestamptz | Có | Mặc định now() | Bắt đầu phụ trách | 2018-06-04 09:20:00+07 | BRD 6.3 |
| `ended_at` | timestamptz | Không | NULL = đang phụ trách; UNIQUE (case_id) WHERE ended_at IS NULL | Kết thúc phụ trách (chuyển người hoặc đóng case) |  | BRD 6.3 mục 7 |

### `app.contact_attempts`

Mỗi dòng là một Attempt append-only. Tài khoản ứng dụng chỉ được INSERT/SELECT; không cấp UPDATE/DELETE. Chỉ assignee hiện tại của case `IN_PROGRESS` được tạo dòng. Attempt không thành công thứ `max_contact` và transition `SKIPPED/UNREACHABLE` phải nằm trong cùng transaction.

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `contact_id` | uuid | Có | PK | Mã Attempt/lần liên lạc | 41c0… | FRD F07 |
| `cycle_id` | uuid | Có | FK → app.review_cycles | Chu kỳ (bộ đếm tính theo chu kỳ) | 3b7c… | BRD 6.8 |
| `case_id` | uuid | Có | FK → app.review_cases | Case (lưu thêm để đọc nhanh) | 9a1e… | BRD 6.6 |
| `attempt_no` | smallint | Có | CHECK (attempt_no >= 1); UNIQUE (cycle_id, attempt_no). Giới hạn trên do backend kiểm theo `max_contact` đang hiệu lực | Lần thứ mấy trong chu kỳ | 2 | BRD 6.6 mục 2 |
| `contacted_at` | timestamptz | Có | Không được ở tương lai | Thời điểm liên lạc | 2018-06-04 11:30:00+07 | BRD 6.6 mục 1 |
| `method` | varchar(20) | Có | CHECK IN ('PHONE','EMAIL','MESSAGE') | Phương thức | PHONE | BRD 6.6 mục 1 |
| `result` | varchar(20) | Có | CHECK IN ('REACHED','NO_ANSWER','CALLBACK','WRONG_NUMBER') | Kết quả lần liên lạc | NO_ANSWER | BRD 6.6 mục 1 |
| `note` | text | Không |  | Ghi lại lời khách | Gọi 2 lần không nghe máy | BRD 6.6 mục 1 |
| `next_contact_date` | date | Không | Mặc định = `retry_gap_days` ngày làm việc sau | Ngày hẹn liên lạc tiếp | 2018-06-05 | BRD 6.6 mục 2 |
| `evidence_ref` | varchar(200) | Không |  | Mã tham chiếu minh chứng (mã cuộc gọi, tiêu đề email) | CL-20180604-117 | Feedback 13/10 |
| `created_by` | uuid | Có | FK → app.users (người đang phụ trách) | Người ghi nhận | 5f0c2b9e-… | BRD 6.6 |
| `created_at` | timestamptz | Có | Mặc định now() | Lúc ghi vào hệ thống | 2018-06-04 11:31:00+07 | BRD 6.6 |

### `app.contact_evidence`

Evidence chỉ là file PNG/JPG/PDF upload qua API, không lưu URL tùy ý làm nguồn minh chứng.

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `evidence_id` | uuid | Có | PK | Mã tệp; chính là `file_id` mà `POST /files` trả về | 77aa… | API contract v0.5 |
| `contact_id` | uuid | Không | FK → app.contact_attempts; tối đa 3 dòng / Attempt (backend kiểm) | NULL từ lúc upload tới khi gắn vào Attempt; tệp không được gắn có thể dọn định kỳ | 41c0… | API contract v0.5 |
| `file_name` | varchar(200) | Có |  | Tên tệp gốc | call-log-0604-1130.png | Feedback 13/10 |
| `file_type` | varchar(50) | Có | CHECK IN ('image/png','image/jpeg','application/pdf') | Loại tệp | image/png | Feedback 13/10 |
| `file_size` | integer | Có | CHECK (file_size <= 5242880) | Dung lượng (byte), tối đa 5 MB | 84210 | Feedback 13/10 |
| `storage_key` | text | Có |  | Vị trí lưu tệp (xem mục 2, điểm 7) | evidence/2018/06/77aa….png | Feedback 13/10 |
| `uploaded_by` | uuid | Có | FK → app.users | Người tải lên | 5f0c2b9e-… | Feedback 13/10 |
| `uploaded_at` | timestamptz | Có | Mặc định now() | Lúc tải lên | 2018-06-04 11:31:00+07 | Feedback 13/10 |

### `app.case_comments` (mới, feedback 13/10)

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `comment_id` | uuid | Có | PK | Mã nhận xét | c1d2… | Feedback 13/10 |
| `case_id` | uuid | Có | FK → app.review_cases | Case | 9a1e… | Feedback 13/10 |
| `author_id` | uuid | Có | FK → app.users; người đang phụ trách hoặc Manager (backend kiểm) | Người viết | 8b2a… | Feedback 13/10 |
| `text` | text | Có | CHECK (char_length(text) BETWEEN 1 AND 1000) | Nội dung nhận xét nội bộ | Khách chưa ưng màu ghế | Feedback 13/10 |
| `created_at` | timestamptz | Có | Mặc định now() | Thời điểm | 2018-06-04 10:05:00+07 | Feedback 13/10 |
| (quy tắc bảng) |  |  | Chỉ INSERT/SELECT | Không sửa, không xoá |  | BRD 6.11 |

### `app.manager_decisions`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `decision_id` | uuid | Có | PK | Mã quyết định | d9e0… | Feedback 13/10 |
| `case_id` | uuid | Có | FK → app.review_cases | Case | 9a1e… | Feedback 13/10 |
| `cycle_id` | uuid | Có | FK → app.review_cycles | Chu kỳ được quyết định | 3b7c… | Feedback 13/10 |
| `decided_by` | uuid | Có | FK → app.users (role MANAGER) | Manager | 8b2a… | Feedback 13/10 |
| `decision` | varchar(30) | Có | CHECK IN ('NO_FURTHER_ACTION','FOLLOW_UP_CUSTOMER','WORK_WITH_SELLER','REFER_AFTER_SALES') | Quyết định (danh mục chờ PO duyệt) | WORK_WITH_SELLER | Feedback 13/10 |
| `reason` | text | Có |  | Lý do ra quyết định | Seller có nhiều case tương tự | BRD 6.12; FRD F12-S03 |
| `next_step` | text | Có |  | Bước tiếp theo | Gửi ảnh đóng gói cho seller | Feedback 13/10 |
| `next_step_assignee_id` | uuid | Không | FK → app.users; user phải active | Người được giao thực hiện bước tiếp theo | 5f0c2b9e-… | BRD 6.12; FRD F12-S03 |
| `due_date` | date | Không | Không ở quá khứ | Hạn | 2018-06-06 | Feedback 13/10 |
| `note` | text | Không |  | Ghi chú | Lần thứ 2 trong tháng | Feedback 13/10 |
| `created_at` | timestamptz | Có | Mặc định now() | Thời điểm | 2018-06-01 16:30:00+07 | Feedback 13/10 |
| (quy tắc bảng) |  |  | Chỉ INSERT/SELECT | Decision không sửa/xóa; bản mới nhất được hiển thị ở Order Detail |  | BRD 6.12 |

### `app.audit_events`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `event_id` | bigint | Có | PK, identity | Mã sự kiện (tăng dần) | 1024 | FRD 4.1 Audit Event |
| `case_id` | uuid | Không | FK → app.review_cases; NULL với PARAMETER_CHANGE | Case liên quan | 9a1e… | BRD 6.8, 6.9 |
| `order_id` | varchar(32) | Không | NULL với PARAMETER_CHANGE | Mã đơn (lưu thêm để lọc nhanh ở màn Audit) | 8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f | F09 |
| `actor_id` | uuid | Có | FK → app.users | Ai thực hiện | 8b2a… | BRD 6.8 |
| `event_type` | varchar(20) | Có | CHECK IN ('CLAIM','ASSIGN','REASSIGN','STATUS','CONTACT','SKIP','REOPEN','OVERRIDE','MODEL_NOTE','COMMENT','DECISION','PARAMETER_CHANGE') | Loại thao tác | REASSIGN | F09-S02 |
| `old_value` | text | Không |  | Giá trị cũ | Trần Thị B | BRD 6.8 |
| `new_value` | text | Có |  | Giá trị mới | Lê Văn C | BRD 6.8 |
| `reason` | text | Khi REASSIGN, REOPEN, OVERRIDE, MODEL_NOTE, DECISION, PARAMETER_CHANGE |  | Lý do / nội dung | B nghỉ chiều nay; C nắm khách miền Bắc | BRD 6.8, 6.9, 6.12 |
| `created_at` | timestamptz | Có | Mặc định now() | Thời điểm | 2018-06-04 09:20:00+07 | BRD 6.8 |
| (quy tắc bảng) |  |  | Chỉ INSERT: tài khoản DB của web không có quyền UPDATE/DELETE | Lịch sử không bao giờ bị sửa hay xoá, kể cả khi đơn được mở lại |  | BRD 6.8; F09-S03 |

### `app.parameter_definitions` (thay `app.config`)

Danh sách tham số được phép cấu hình và khoảng giá trị hợp lệ. Dữ liệu tĩnh, nhóm phát triển tạo sẵn.

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `param_key` | varchar(40) | Có | PK | Mã tham số | capacity | FRD F10-S01 |
| `unit` | varchar(10) | Có | CHECK IN ('hours','days','orders','times','enum') | Đơn vị | orders | FRD F10-S01 |
| `min_value`, `max_value` | integer | Khi unit ≠ 'enum' |  | Khoảng hợp lệ | 1; 20 | FRD F10-S02 |
| `allowed_values` | text[] | Khi unit = 'enum' |  | Giá trị hợp lệ | {CALENDAR,BUSINESS_HOURS} | BRD 6.7 |
| `in_brd` | boolean | Có |  | true = F10-S02 có liệt kê; false = đề xuất bổ sung | true | — |
| `description` | text | Có |  | Mô tả hiển thị | Số đơn Đang xử lý tối đa / nhân viên | FRD F10-S01 |

Giá trị ban đầu: `sla_calendar` = CALENDAR; `sla_hours_high` = 4; `sla_hours_medium` = 24; `sla_hours_low` = 48; `first_touch_hours` = 2; `capacity` = 5; `capacity_warn` = 4;
`max_contact` = 3; `retry_gap_days` = 1; `soon_hours` = 2; `stale_hours` = 24; `aging_days` = 2; `reopen_review_days` = 7; `reopen_review_times` = 2.

### `app.parameters` (thay `app.config`)

Mỗi dòng là **một phiên bản** của một tham số. Giá trị đang hiệu lực tại thời điểm t = phiên bản mới nhất có `effective_at ≤ t`.

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `parameter_id` | bigint | Có | PK, identity | Mã dòng | 15 | BRD 6.9 |
| `param_key` | varchar(40) | Có | FK → app.parameter_definitions | Tham số | capacity | BRD 6.9 mục 2 |
| `version` | integer | Có | UNIQUE (param_key, version) | Phiên bản, tăng dần theo tham số | 2 | BRD 6.9 mục 2 |
| `value` | text | Có | Kiểm theo `parameter_definitions` | Giá trị mới | 6 | BRD 6.9 mục 2 |
| `effective_at` | timestamptz | Có | Không ở quá khứ khi tạo | Thời điểm có hiệu lực (tương lai = đã lên lịch) | 2018-06-08 08:00:00+07 | BRD 6.9 mục 2–4 |
| `actor_id` | uuid | Có | FK → app.users (role MANAGER) | Người đổi | 8b2a… | BRD 6.9 mục 1–2 |
| `reason` | text | Có |  | Lý do | Thêm ca chiều từ 08/06 | BRD 6.9 mục 2 |
| `created_at` | timestamptz | Có | Mặc định now() | Lúc tạo phiên bản | 2018-06-04 09:50:00+07 | BRD 6.9 mục 2 |
| (quy tắc bảng) |  |  | Chỉ INSERT | Không sửa/xoá phiên bản cũ; giá trị cũ = phiên bản `version - 1` |  | F10-S04 |

### `ml.model_thresholds` (ngưỡng theo release ML)

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `threshold_version` | varchar(20) | Có | PK cùng `model_release_id` | Phiên bản bộ ngưỡng; định danh đầy đủ là `(release_version, threshold_version)` | thr-v1 | Model release |
| `model_version` | varchar(50) | Có |  | Model mà ngưỡng được chọn trên validation | hd-item-v1 | Model registry |
| `high_from`, `medium_from` | numeric(18,17) | Có | `1 >= high_from > medium_from >= 0` | Ranh giới level | 0.700; 0.450 | Validation policy |
| `selection_policy` | varchar(50) | Có |  | Quy tắc chọn ngưỡng, không chỉnh trên test | validation-f1-v1 | Experiment config |
| `created_at` | timestamptz | Có |  | Thời điểm phát hành | 2026-10-21T00:00:00Z | Model registry |

### `ml.v_risk_orders_for_web` (view cấp đơn, bên ML/DW cung cấp)

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `order_id` | varchar(32) | Có |  | Mã đơn | a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30 | Inference contract; gold |
| `prediction_id` | uuid | Có |  | Mã lần dự đoán | c2d4… | Inference contract; gold |
| `risk_score` | numeric(4,3) | Có | 0–1 | Điểm **tổng hợp** của đơn (web không bao giờ sửa) | 0.910 | BRD 6.1 mục 3 |
| `risk_level` | varchar(10) | Có | HIGH / MEDIUM / LOW | Mức rủi ro theo ngưỡng | HIGH | BRD 6.1 mục 4 |
| `aggregation_rule` | varchar(20) | Có |  | Quy tắc tổng hợp + version | max-v1 | BRD 6.1 mục 3–4 |
| `items_count` | smallint | Có |  | Số sản phẩm trong đơn (view alias của `item_count`) | 3 | FRD F04-S03 |
| `top_factors` | jsonb | Không | Mảng chuỗi; rỗng nếu model chưa trả | Yếu tố liên quan/giải thích, không phải quan hệ nhân quả | ["Seller took 5 days to hand over"] | Inference contract |
| `suggested_action` | varchar(30) | Có | CONTACT / MONITOR / NO_ACTION | Đề xuất của model (chỉ tham khảo) | CONTACT | BRD 6.1 mục 6 |
| `model_version` | varchar(50) | Có |  | Phiên bản model | hd-model v0.3 | Inference contract |
| `threshold_version` | varchar(20) | Có |  | Phiên bản ngưỡng HIGH/MEDIUM | thr-v1 | BRD 6.1 mục 4 |
| `predicted_at` | timestamptz | Có |  | Thời điểm dự đoán | 2018-06-04 08:00:00+07 | Inference contract |
| `seller_id` | varchar(32) | Có |  | Mã seller | 7c67e1448b00f6e969d365cea6b010ab | gold |
| `category` | varchar(60) | Có |  | Ngành hàng chính của đơn (mã Olist) | office_furniture | gold |
| `customer_city`, `customer_state` | varchar | Có |  | Thành phố / bang của khách | Rio de Janeiro, RJ | gold |
| `order_value`, `freight` | numeric(10,2) | Có |  | Giá trị đơn, phí ship (R$) | 459.90; 42.30 | gold |
| `purchase_at`, `approved_at`, `carrier_at`, `delivered_at`, `estimated_at` | timestamptz | Có | Chỉ dữ liệu có trước mốc dự báo | Mốc thời gian đơn (dòng thời gian ở Order Detail) | 2018-05-14 … | gold |

### `ml.v_risk_items_for_web` (view cấp sản phẩm, mới)

Review Olist tồn tại ở cấp order. Trong training, mọi item của cùng order kế thừa cùng nhãn review; split và bootstrap group theo `order_id`. Vì vậy score item chỉ biểu thị rủi ro review thấp của order trong bối cảnh item và không được diễn giải là xác suất item gây bất mãn.

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `product_item_id` | varchar(40) | Có | Duy nhất; = order_id + '-' + order_item_id | Mã sản phẩm trong đơn | a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30-2 | BRD 6.1 mục 2 |
| `order_id` | varchar(32) | Có | Khớp `ml.v_risk_orders_for_web.order_id` | Mã đơn | a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30 | BRD 6.1 mục 2 |
| `order_item_id` | smallint | Có |  | Số thứ tự sản phẩm trong đơn (Olist) | 2 | Olist order_items |
| `product_id` | varchar(32) | Có |  | Mã sản phẩm Olist | 9f2d… | Olist products |
| `category` | varchar(60) | Có |  | Ngành hàng sản phẩm | office_furniture | Olist products |
| `price` | numeric(10,2) | Có |  | Giá sản phẩm (R$) | 129.00 | Olist order_items |
| `weight_g` | integer | Không |  | Cân nặng (g) | 6100 | Olist products |
| `photos` | smallint | Không |  | Số ảnh sản phẩm | 4 | Olist products |
| `prediction_id` | uuid | Có |  | Lần dự đoán | c2d4… | Inference contract |
| `risk_score` | numeric(4,3) | Có | 0–1 | Điểm của sản phẩm (web không bao giờ sửa) | 0.620 | BRD 6.1 mục 2 |
| `risk_level` | varchar(10) | Có | HIGH / MEDIUM / LOW | Mức rủi ro của sản phẩm | MEDIUM | BRD 6.1 mục 4 |
| `top_factors` | jsonb | Không | Rỗng nếu model chưa trả | Yếu tố liên quan của sản phẩm | ["Heavy item shipped over 1,500 km"] | FRD F04-S04 |
| `suggested_action` | varchar(30) | Có | CONTACT / MONITOR / NO_ACTION | Đề xuất cho sản phẩm | MONITOR | BRD 6.1 mục 6 |
| `model_version` | varchar(50) | Có |  | Phiên bản model sản phẩm | hd-item v0.3 | BRD 7 (truy vết) |
| `predicted_at` | timestamptz | Có |  | Thời điểm dự đoán | 2018-06-04 08:00:00+07 | BRD 7 (truy vết) |
| `synthetic_data_flag` | boolean | Có | Mặc định false | Chi tiết sản phẩm giả lập vì dữ liệu gốc thiếu | true | BRD 4.1; FRD 4.1 |
| `data_source` | varchar(30) | Có | 'olist_order_items' / 'synthetic_v1' | Nguồn dữ liệu của dòng | synthetic_v1 | BRD 7 (truy vết) |

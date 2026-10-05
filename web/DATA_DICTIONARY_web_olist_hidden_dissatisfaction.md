# BẢNG MÔ TẢ DỮ LIỆU PHẦN WEB (DATA DICTIONARY)

## Hệ thống nhận diện và ưu tiên đơn hàng có nguy cơ bất mãn ẩn

| Thuộc tính | Nội dung |
|---|---|
| Phiên bản | 0.1 |
| Trạng thái | Bản nháp, chờ duyệt: Quân (khớp ERD), Trung (kiểu dữ liệu PostgreSQL, khoá chính/khoá ngoại), Huy (phần view đọc từ ML) |
| Ngày | 05/10/2026 |
| Nguồn | Tab DATA DICTIONARY WEB trong sheet phân công của nhóm. Sửa ở đây hoặc ở sheet thì cập nhật cả hai cho khớp |
| Tài liệu liên quan | BRD v3.0; FRD v1.0; API_CONTRACT_olist_hidden_dissatisfaction.md; ERD – TBD |

## 1. Phạm vi

- **Schema `app`**: các bảng của web (tài khoản, case xử lý, phân công, lần liên lạc, audit, cấu hình). Web được đọc và ghi.
- **View `ml.v_risk_orders_for_web`**: kết quả dự đoán và bối cảnh đơn do bên ML/Data Warehouse cung cấp. Web chỉ đọc, không bao giờ sửa risk score.
- Dữ liệu Olist gốc (bronze/silver/gold) nằm ở bản mô tả của Quân + Đào bên ML, không lặp lại ở đây.

Tên cột và các mã (`SPECIALIST`, `PHONE`, `CONTACT`…) trong tài liệu này cũng là tên field và mã dùng trong API contract.

## 2. Điểm cần nhóm xem

1. **`contact_attempts.attempt_no` đang `CHECK 1–3` cố định trong database**, trong khi số lần tối đa lại nằm ở `app.config.max_contact` (đổi được, BRD 6.7 yêu cầu cấu hình có version). Nếu sau này đổi thành 4 lần thì database chặn. Đề xuất: `CHECK (attempt_no >= 1)`, giới hạn trên do backend kiểm theo `max_contact`.
2. **Chưa có chỗ chứa giá trị ngưỡng HIGH/MEDIUM** (0,70 và 0,45). View chỉ có `threshold_version`, nhưng màn Order Detail hiện "HIGH ≥ 0,7, MEDIUM ≥ 0,45". Cần thêm 2 cột ngưỡng vào view hoặc một bảng ngưỡng bên ML (hỏi Huy).
3. **`review_cases.sla_due_at` được lưu sẵn**, nên khi Manager mở lại case (`queued_at` đặt lại) backend phải tính lại cột này. Ngoài ra BRD 6.7 muốn SLA tính theo ngày làm việc (bỏ cuối tuần, ngày lễ), không phải cộng giờ đồng hồ.
4. **`close_note` chỉ ghi là bắt buộc khi `skip_reason = 'OTHER'`**, nhưng form Hoàn tất cũng có ô ghi chú. Đề xuất: `close_note` dùng cho cả hoàn tất và bỏ qua, không bắt buộc, trừ trường hợp `OTHER`.
5. **Đăng nhập bằng session hay JWT** (dòng "Chốt công nghệ backend"): nếu chọn session lưu ở database thì cần thêm bảng `app.sessions`.
6. **Múi giờ**: cột lưu `timestamptz`, ví dụ đang ghi `+07`, nhưng dữ liệu Olist là giờ Brazil (`-03`). Cần chốt hiển thị theo giờ nào (cũng là điểm 1 ở mục 7 của API contract).

## 3. Các bảng

### `app.users`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `user_id` | uuid | Có | PK, mặc định gen_random_uuid() | Mã người dùng | 5f0c2b9e-… | FRD 4.1 User/Role; BRD 3 |
| `username` | varchar(50) | Có | UNIQUE | Tên đăng nhập, tài khoản tạo sẵn (không có đăng ký) | nhanvien | FRD 4.1 User/Role; BRD 3 |
| `password_hash` | text | Có |  | Mật khẩu đã băm (bcrypt/argon2), không lưu mật khẩu thô | $2b$12$… | FRD 4.1 User/Role; BRD 3 |
| `full_name` | varchar(100) | Có |  | Họ tên hiện trên giao diện | Trần Thị B | FRD 4.1 User/Role; BRD 3 |
| `role` | varchar(20) | Có | CHECK IN ('SPECIALIST','MANAGER') | Vai, quyết định màn và quyền thao tác | SPECIALIST | FRD 4.1 User/Role; BRD 3 |
| `is_active` | boolean | Có | Mặc định true | Tắt tài khoản thay vì xoá (giữ lịch sử audit) | true | FRD 4.1 User/Role; BRD 3 |
| `created_at` | timestamptz | Có | Mặc định now() | Thời điểm tạo tài khoản | 2018-05-01 08:00:00+07 | FRD 4.1 User/Role; BRD 3 |

### `app.review_cases`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `case_id` | uuid | Có | PK | Mã case xử lý (1 đơn có thể có nhiều case nếu bị đưa lại vào queue) | 9a1e… | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `order_id` | varchar(32) | Có | FK → đơn hàng Olist (gold); UNIQUE khi status chưa đóng | Mã đơn Olist | a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30 | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `prediction_id` | uuid | Có | FK → ml.predictions | Lần dự đoán đưa đơn vào queue (giữ đúng score/model lúc đó) | c2d4… | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `status` | varchar(20) | Có | CHECK IN ('PENDING','IN_PROGRESS','COMPLETED','SKIPPED'); mặc định 'PENDING' | Trạng thái xử lý | IN_PROGRESS | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `assignee_id` | uuid | Không | FK → app.users; NULL khi PENDING | Người đang phụ trách | 5f0c2b9e-… | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `queued_at` | timestamptz | Có |  | Lúc vào Risk Queue (mốc tính SLA và aging) | 2018-06-04 11:00:00+07 | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `sla_due_at` | timestamptz | Có | Tính bằng queued_at + giờ SLA theo mức rủi ro (lấy từ app.config) | Hạn SLA | 2018-06-04 15:00:00+07 | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `outcome` | varchar(30) | Khi COMPLETED | CHECK IN ('HAS_ISSUE','NO_ISSUE','UNREACHABLE','DUPLICATE'); bắt buộc khi status='COMPLETED' | Kết quả khi hoàn tất | NO_ISSUE | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `skip_reason` | varchar(30) | Khi SKIPPED | CHECK IN ('UNREACHABLE','DUPLICATE','REFUSED','NOT_APPLICABLE','OTHER'); bắt buộc khi status='SKIPPED' | Lý do bỏ qua (danh mục chờ PO duyệt) | UNREACHABLE | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `close_note` | text | Khi skip_reason='OTHER' |  | Ghi chú khi đóng case | Khách đã đổi số điện thoại | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `closed_at` | timestamptz | Khi đã đóng |  | Lúc hoàn tất hoặc bỏ qua | 2018-06-04 16:10:00+07 | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `reopen_count` | smallint | Có | Mặc định 0 | Số lần Manager mở lại (≥ 2 lần thì bắt buộc review) | 1 | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `updated_at` | timestamptz | Có | Mặc định now(), cập nhật mỗi thao tác | Lần cập nhật gần nhất (≥ 1 ngày không đổi → cảnh báo) | 2018-06-04 11:30:00+07 | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |
| `row_version` | integer | Có | Mặc định 0, tăng mỗi lần sửa | Khoá lạc quan: 2 người cùng claim thì chỉ người đầu tiên thành công (409 cho người sau) | 3 | FRD 4.1 Review Status, Review Outcome; BRD 6.4–6.7 |

### `app.assignments`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `assignment_id` | uuid | Có | PK | Mã lần phân công | e71b… | FRD 4.1 Review Assignment; BRD 6.3 |
| `case_id` | uuid | Có | FK → app.review_cases | Case được phân công | 9a1e… | FRD 4.1 Review Assignment; BRD 6.3 |
| `assignee_id` | uuid | Có | FK → app.users (role SPECIALIST) | Người nhận | 5f0c2b9e-… | FRD 4.1 Review Assignment; BRD 6.3 |
| `assigned_by` | uuid | Có | FK → app.users | Người thực hiện (chính Specialist khi CLAIM, Manager khi ASSIGN/REASSIGN) | 8b2a… | FRD 4.1 Review Assignment; BRD 6.3 |
| `method` | varchar(20) | Có | CHECK IN ('CLAIM','ASSIGN','REASSIGN') | Cách nhận đơn | CLAIM | FRD 4.1 Review Assignment; BRD 6.3 |
| `override_capacity` | boolean | Có | Mặc định false | Manager giao vượt giới hạn 5 đơn | false | FRD 4.1 Review Assignment; BRD 6.3 |
| `reason` | text | Khi REASSIGN hoặc override |  | Lý do chuyển người / vượt capacity | B nghỉ chiều nay | FRD 4.1 Review Assignment; BRD 6.3 |
| `started_at` | timestamptz | Có | Mặc định now() | Bắt đầu phụ trách | 2018-06-04 09:20:00+07 | FRD 4.1 Review Assignment; BRD 6.3 |
| `ended_at` | timestamptz | Không | NULL = đang phụ trách; UNIQUE (case_id) WHERE ended_at IS NULL | Kết thúc phụ trách (chuyển người hoặc đóng case) |  | FRD 4.1 Review Assignment; BRD 6.3 |

### `app.contact_attempts`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `contact_id` | uuid | Có | PK | Mã lần liên lạc | 41c0… | FRD 4.1 Review Activity; BRD 6.6 |
| `case_id` | uuid | Có | FK → app.review_cases | Case | 9a1e… | FRD 4.1 Review Activity; BRD 6.6 |
| `attempt_no` | smallint | Có | CHECK 1–3; UNIQUE (case_id, attempt_no) | Lần thứ mấy (tối đa 3) | 2 | FRD 4.1 Review Activity; BRD 6.6 |
| `contacted_at` | timestamptz | Có | Không được ở tương lai | Thời điểm liên lạc | 2018-06-04 11:30:00+07 | FRD 4.1 Review Activity; BRD 6.6 |
| `method` | varchar(20) | Có | CHECK IN ('PHONE','EMAIL','MESSAGE') | Phương thức | PHONE | FRD 4.1 Review Activity; BRD 6.6 |
| `result` | varchar(20) | Có | CHECK IN ('REACHED','NO_ANSWER','CALLBACK','WRONG_NUMBER') | Kết quả lần liên lạc | NO_ANSWER | FRD 4.1 Review Activity; BRD 6.6 |
| `note` | text | Không |  | Ghi lại lời khách | Gọi 2 lần không nghe máy | FRD 4.1 Review Activity; BRD 6.6 |
| `next_contact_date` | date | Không | Mặc định = 1 ngày làm việc sau | Ngày hẹn liên lạc tiếp | 2018-06-05 | FRD 4.1 Review Activity; BRD 6.6 |
| `created_by` | uuid | Có | FK → app.users (người đang phụ trách) | Người ghi nhận | 5f0c2b9e-… | FRD 4.1 Review Activity; BRD 6.6 |
| `created_at` | timestamptz | Có | Mặc định now() | Lúc ghi vào hệ thống | 2018-06-04 11:31:00+07 | FRD 4.1 Review Activity; BRD 6.6 |

### `app.audit_events`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `event_id` | bigint | Có | PK, identity | Mã sự kiện (tăng dần) | 1024 | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `case_id` | uuid | Có | FK → app.review_cases | Case liên quan | 9a1e… | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `order_id` | varchar(32) | Có |  | Mã đơn (lưu thêm để lọc nhanh ở màn Audit) | 8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `actor_id` | uuid | Có | FK → app.users | Ai thực hiện | 8b2a… | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `event_type` | varchar(20) | Có | CHECK IN ('CLAIM','ASSIGN','REASSIGN','STATUS','CONTACT','SKIP','REOPEN','OVERRIDE','MODEL_NOTE') | Loại thao tác | REASSIGN | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `old_value` | text | Không |  | Giá trị cũ | Trần Thị B | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `new_value` | text | Có |  | Giá trị mới | Lê Văn C | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `reason` | text | Khi REASSIGN, REOPEN, OVERRIDE, MODEL_NOTE |  | Lý do / nội dung ghi chú model review | B nghỉ chiều nay; C nắm khách miền Bắc | FRD 4.1 Audit Event; BRD 6.8; F09 |
| `created_at` | timestamptz | Có | Mặc định now() | Thời điểm | 2018-06-04 09:20:00+07 | FRD 4.1 Audit Event; BRD 6.8; F09 |
| (quy tắc bảng) |  |  | Chỉ INSERT: tài khoản DB của web không có quyền UPDATE/DELETE | Lịch sử không bao giờ bị sửa hay xoá, kể cả khi mở lại đơn |  | BRD 6.8; F09-S03 |

### `app.config`

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `config_version` | varchar(20) | Có | PK | Phiên bản cấu hình | cfg-v1 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `effective_from` | date | Có |  | Ngày bắt đầu áp dụng | 2018-05-01 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `owner` | varchar(100) | Có |  | Người chịu trách nhiệm thay đổi | Product Owner | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `is_active` | boolean | Có | UNIQUE WHERE is_active | Cấu hình đang dùng (chỉ 1 dòng) | true | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `capacity` | smallint | Có | Mặc định 5 | Số đơn tối đa đang xử lý / Specialist | 5 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `capacity_warn` | smallint | Có | Mặc định 4 | Từ đơn thứ mấy thì cảnh báo | 4 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `max_contact` | smallint | Có | Mặc định 3 | Số lần liên lạc tối đa | 3 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `retry_gap_days` | smallint | Có | Mặc định 1 | Khoảng cách giữa 2 lần liên lạc (ngày làm việc) | 1 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `sla_hours_high` | smallint | Có | Mặc định 4 | Giờ SLA mức HIGH | 4 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `sla_hours_medium` | smallint | Có | Mặc định 24 | Giờ SLA mức MEDIUM | 24 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `sla_hours_low` | smallint | Có | Mặc định 48 | Giờ SLA mức LOW | 48 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `soon_hours` | smallint | Có | Mặc định 2 | Còn dưới bao nhiêu giờ thì báo "sắp hết hạn" | 2 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `stale_hours` | smallint | Có | Mặc định 24 | Đang xử lý bao lâu không cập nhật thì cảnh báo | 24 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `aging_days` | smallint | Có | Mặc định 2 | Nằm queue bao lâu thì escalation | 2 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `reopen_review_days` | smallint | Có | Mặc định 7 | Mở lại sau bao nhiêu ngày thì bắt buộc review | 7 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |
| `reopen_review_times` | smallint | Có | Mặc định 2 | Mở lại quá bao nhiêu lần thì bắt buộc review | 2 | FRD 4.1 Threshold Configuration; BRD 6.3, 6.6, 6.7 |

### `ml.v_risk_orders_for_web` (view, bên ML/DW cung cấp)

| Cột | Kiểu | Bắt buộc | Khoá / ràng buộc / mặc định | Ý nghĩa | Ví dụ | Nguồn |
|---|---|---|---|---|---|---|
| `order_id` | varchar(32) | Có |  | Mã đơn | a3f9c1e27b8d4e0f9c2b6d1e8f7a5c30 | Inference contract (Huy); gold (Trung, Quân) |
| `prediction_id` | uuid | Có |  | Mã lần dự đoán | c2d4… | Inference contract (Huy); gold (Trung, Quân) |
| `risk_score` | numeric(4,3) | Có | 0–1 | Điểm rủi ro (web không bao giờ sửa) | 0.910 | Inference contract (Huy); gold (Trung, Quân) |
| `risk_level` | varchar(10) | Có | HIGH / MEDIUM / LOW | Mức rủi ro theo ngưỡng | HIGH | Inference contract (Huy); gold (Trung, Quân) |
| `top_factors` | jsonb | Không | Mảng chuỗi; rỗng nếu model chưa trả | Yếu tố liên quan (hiển thị nguyên văn) | ["Seller took 5 days to hand over"] | Inference contract (Huy); gold (Trung, Quân) |
| `suggested_action` | varchar(30) | Có | CONTACT / MONITOR / NO_ACTION | Đề xuất của model (chỉ tham khảo) | CONTACT | Inference contract (Huy); gold (Trung, Quân) |
| `model_version` | varchar(50) | Có |  | Phiên bản model | hd-model v0.3 | Inference contract (Huy); gold (Trung, Quân) |
| `threshold_version` | varchar(20) | Có |  | Phiên bản ngưỡng HIGH/MEDIUM | thr-v1 | Inference contract (Huy); gold (Trung, Quân) |
| `predicted_at` | timestamptz | Có |  | Thời điểm dự đoán | 2018-06-04 08:00:00+07 | Inference contract (Huy); gold (Trung, Quân) |
| `seller_id` | varchar(32) | Có |  | Mã seller | 7c67e1448b00f6e969d365cea6b010ab | Inference contract (Huy); gold (Trung, Quân) |
| `category` | varchar(60) | Có |  | Ngành hàng (mã Olist) | office_furniture | Inference contract (Huy); gold (Trung, Quân) |
| `customer_city`, `customer_state` | varchar | Có |  | Thành phố / bang của khách | Rio de Janeiro, RJ | Inference contract (Huy); gold (Trung, Quân) |
| `order_value`, `freight` | numeric(10,2) | Có |  | Giá trị đơn, phí ship (R$) | 459.90; 42.30 | Inference contract (Huy); gold (Trung, Quân) |
| `purchase_at`, `approved_at`, `carrier_at`, `delivered_at`, `estimated_at` | timestamptz | Có | Chỉ dữ liệu có trước mốc dự báo | Mốc thời gian đơn (dòng thời gian ở Order Detail) | 2018-05-14 … | Inference contract (Huy); gold (Trung, Quân) |

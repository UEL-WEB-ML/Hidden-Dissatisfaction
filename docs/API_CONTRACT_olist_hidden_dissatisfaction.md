# TÀI LIỆU API (API CONTRACT)

## Hệ thống hỗ trợ chăm sóc khách hàng cho đơn hàng và sản phẩm có nguy cơ bất mãn ẩn

| Thuộc tính | Nội dung |
|---|---|
| Phiên bản | 0.5 |
| Trạng thái | Bản nháp, Frontend và Backend cùng chốt |
| Ngày | 21/10/2026 |
| Tài liệu liên quan | BRD_olist_hidden_dissatisfaction.md (v4.2); FRD_olist_hidden_dissatisfaction.md (v2.2); DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md (v0.5); ERD – TBD |
| Bản chạy thử | Chưa được lưu trong repository hiện tại; mock/frontend phải được cập nhật và kiểm tra theo contract v0.5 trước khi tuyên bố tương thích |

### Thay đổi so với v0.4 (21/10)

- Chuẩn hóa UI Attempt thành contact record append-only; chỉ assignee hiện tại được thêm.
- Evidence chỉ nhận file PNG/JPG/PDF qua `POST /files`, không nhận URL tùy ý.
- Bỏ `UNREACHABLE` khỏi completed outcome; Attempt không thành công cuối cùng tự chuyển case sang `SKIPPED/UNREACHABLE`.
- Manager Decision bắt buộc `reason`, hỗ trợ `next_step_assignee_id` tùy chọn và luôn append-only.
- Cập nhật traceability sang BRD 4.2, FRD 2.2 và F12.

### Thay đổi so với v0.3 (14/10)

- Chốt Product Item Risk Output là đơn vị ML và Order Risk Case là đơn vị workflow.
- Chốt `max-v1`: điểm order bằng điểm product item cao nhất trong order.
- Làm rõ item kế thừa nhãn review cấp order; score không chứng minh item gây bất mãn.
- Ngưỡng LOW/MEDIUM/HIGH do pipeline chọn trên validation, phát hành cùng định danh `(release_version, threshold_version)`; các số trong ví dụ không phải hằng số nghiệp vụ.

### Thay đổi so với v0.2 (13/10)

Đợt này làm cho Backend dễ nối vào mà không phải chốt trước với Frontend: chỗ nào chưa chốt thì Frontend nhận được cả hai cách.

| Nội dung | Mục |
|---|---|
| Thêm `POST /files` (multipart, field `file`) trả `file_id`; `evidence` trong `/contacts` gửi `file_id` thay vì chỉ metadata | 3.3, 4.5 |
| Thời gian: Frontend đọc được cả `"YYYY-MM-DD HH:mm"` lẫn ISO 8601 có múi giờ | 2.1 |
| Đăng nhập: Frontend chạy được cả token Bearer lẫn session cookie (chọn trong `js/config.js`) | 2.2 |
| `GET /config` thêm `typical_order` (mức thường gặp để so sánh ở Chi tiết đơn), trước đây ghi cứng trong trang | 4.2 |
| Mục 6 viết lại: Backend chỉ sửa `js/config.js`, có backend giả chạy qua HTTP và trang tự kiểm tra API | 6 |

### Thay đổi so với v0.1 (05/10)

| Nội dung | Lý do |
|---|---|
| Thêm output ML theo từng sản phẩm (`items`, `top_item`, `aggregation_rule`, `synthetic_data_flag`) | BRD 6.1 mục 2–3, FRD F02-S02, F04-S03/S04 |
| Thêm review cycle: `cycle_no`, `original_queued_at`, `cycles`; mở lại thì reset bộ đếm liên lạc và SLA | BRD 6.8, FRD F08-S01 |
| Thêm `GET/POST /parameters`, `parameter_version`; bỏ mọi con số ghi cứng (5 đơn, 3 lần…) | BRD 6.9, FRD F10 |
| Specialist không tự nhận đơn HIGH: `self_claim_allowed`, lỗi `403 HIGH_RISK_REQUIRES_ASSIGN` | BRD 6.3 mục 1, FRD F02-S04, F05-S01 |
| Thêm `PATCH /me` (`preferred_language`), header `Accept-Language` cho câu lỗi | FRD F11 |
| Dashboard: `view=order|product`, `product_item`, `trend` | FRD F01-S01, S02, S08 |
| Tìm theo Product Item ID qua `q` | FRD F03-S01 |
| Thêm nhận xét (`/comments`), quyết định của Manager (`/decisions`), minh chứng liên lạc (`evidence`) | Đã chuẩn hóa và sau đó cập nhật tại BRD 6.11–6.12, FRD F07/F08-S05/F12 |
| Audit thêm `COMMENT`, `DECISION`, `PARAMETER_CHANGE`; `order_id` có thể `null` | FRD F09-S02 |

## 1. Mục đích và nguyên tắc

Tài liệu này là thỏa thuận giữa Frontend và Backend: mỗi endpoint nhận gì, trả gì, lỗi thì trả mã nào.
Hai bên làm song song theo tài liệu này. Frontend, mock server và Backend chỉ được tuyên bố tương thích sau khi vượt contract check v0.5. Các đường dẫn `web/Prototype/...` bên dưới là cấu trúc triển khai mục tiêu; chúng chưa nằm trong repository hiện tại.

Nguyên tắc:

1. **Backend là nơi kiểm tra luật nghiệp vụ** (BRD mục 6): quyền theo vai, HIGH chỉ Manager giao, capacity, số lần liên lạc, chuyển trạng thái hợp lệ, bắt buộc lý do. Frontend ẩn nút trái quyền cho dễ dùng, nhưng Backend vẫn kiểm tra lại mọi request (FRD mục 3).
2. **Không ghi cứng con số vận hành.** Capacity, số lần liên lạc, SLA… lấy từ bộ tham số đang hiệu lực (`GET /config`), do Manager đổi ở `POST /parameters` (BRD 6.9).
3. **Backend tính sẵn các số phụ thuộc thời gian** (SLA, aging, escalation, stale) và số liệu Dashboard, vì bản thật phải tính theo lịch SLA đã cấu hình (BRD 6.7). Frontend chỉ hiển thị.
4. **Không endpoint nào sửa được risk score, risk level hay output gốc của model**, ở cả cấp đơn và cấp sản phẩm (BRD 6.1 mục 5, FRD F08-S04).
5. **Mọi thao tác ghi đều tạo audit event** ở Backend; không có endpoint sửa hay xóa audit (BRD 6.8, FRD F09-S03).

Tên field và các mã (`SPECIALIST`, `PHONE`, `CONTACT`…) theo **DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md**, để Backend đọc ghi PostgreSQL không phải đổi tên qua lại.

## 2. Quy ước chung

### 2.1. Địa chỉ và định dạng

- Base URL: `/api/v1` (máy dev: `http://localhost:8000/api/v1`).
- Request và response đều là JSON, UTF-8. Tên field viết `snake_case`.
- Thời gian dạng `"YYYY-MM-DD HH:mm"`, ngày dạng `"YYYY-MM-DD"`, theo giờ của hệ thống (xem mục 7, điểm 1).
  Frontend **đọc được cả ISO 8601 có múi giờ** (`"2018-06-04T14:00:00Z"`, `"2018-06-04T14:00:00+07:00"`) và hiển thị theo giờ máy người xem,
  nên Backend trả dạng nào cũng được. Frontend **gửi lên** dạng `"YYYY-MM-DD HH:mm"` (ô nhập giờ của trình duyệt không kèm múi giờ).
- Mã trạng thái, mức rủi ro, outcome… gửi bằng mã (`IN_PROGRESS`, `HAS_ISSUE`), Frontend tự đổi sang nhãn hiển thị theo ngôn ngữ đang chọn.

### 2.2. Xác thực

- `POST /auth/login` trả `token`. Mọi request khác gửi header `Authorization: Bearer <token>`.
- Nếu Backend dùng **session cookie** thay cho token: đặt `AUTH: "cookie"` trong `js/config.js`. Khi đó Frontend không gửi header `Authorization`
  mà gửi kèm cookie (`credentials: "include"`); `POST /auth/login` không cần trả `token`, chỉ cần trả `user` và đặt cookie.
  Khác cổng/khác domain thì Backend phải bật CORS có `Access-Control-Allow-Credentials: true` và cookie `SameSite` phù hợp.
- Thiếu token hoặc token hết hạn: `401 UNAUTHENTICATED`, Frontend đưa người dùng về màn Đăng nhập.
- Vai (`SPECIALIST` | `MANAGER`) gắn với tài khoản, người dùng không tự chọn.

### 2.3. Ngôn ngữ (FRD F11)

- Mọi request gửi header `Accept-Language: vi` hoặc `en` (ngôn ngữ giao diện đang chọn).
- Backend dùng header này **chỉ để chọn ngôn ngữ của `error.message`**. Mã, số, ID, giá trị tham số và audit lưu trong database không đổi theo ngôn ngữ (F11-S03).
- Nhãn trạng thái, outcome… do Frontend dịch. Văn bản do model sinh (`top_factors`) và văn bản người dùng nhập (ghi chú, lý do) hiển thị nguyên văn.

### 2.4. Lỗi

Mọi lỗi có cùng một dạng:

```json
{ "error": { "code": "CAPACITY_FULL", "message": "Bạn đang giữ đủ 5 đơn. Hoàn tất hoặc bỏ qua một đơn rồi mới nhận thêm.", "details": null } }
```

`message` là câu hiển thị thẳng cho người dùng, theo `Accept-Language`. `details` có thể chứa `field` (ô nhập bị lỗi) hoặc dữ liệu thêm.

| HTTP | `code` | Khi nào |
|---|---|---|
| 400 | `INVALID_ORDER_ID` | `q` không phải tiền tố mã đơn (0-9, a-f, ≤ 32 ký tự) và cũng không phải Product Item ID (`<32 ký tự>-<số>`) |
| 401 | `INVALID_CREDENTIALS` | Sai tên đăng nhập hoặc mật khẩu |
| 401 | `UNAUTHENTICATED` | Thiếu token hoặc token hết hạn |
| 403 | `FORBIDDEN` | Vai không được làm thao tác này (vd Specialist gọi `/dashboard`, `/parameters`) |
| 403 | `HIGH_RISK_REQUIRES_ASSIGN` | Specialist bấm nhận đơn HIGH (BRD 6.3 mục 1) |
| 404 | `ORDER_NOT_FOUND` | Không có đơn với mã này |
| 409 | `ALREADY_CLAIMED` | Hai người cùng nhận một đơn, người sau nhận lỗi này (FRD F05-S03) |
| 409 | `INVALID_STATE` | Chuyển trạng thái không hợp lệ (vd hoàn tất đơn đang Pending) |
| 422 | `VALIDATION_ERROR` | Thiếu hoặc sai dữ liệu bắt buộc |
| 422 | `REASON_REQUIRED` | Reassign, override, mở lại, Manager Decision hoặc đổi tham số mà không có lý do |
| 422 | `CAPACITY_FULL` | Người nhận đã giữ đủ `capacity` đơn (BRD 6.3) |
| 422 | `MAX_CONTACTS_REACHED` | Chu kỳ hiện tại đã đủ `max_contact` lần liên lạc (BRD 6.6) |
| 422 | `REVIEW_CONFIRMATION_REQUIRED` | Mở lại case đóng quá `reopen_review_days` ngày hoặc đã mở lại từ `reopen_review_times` lần mà chưa xác nhận (BRD 6.7) |
| 422 | `EVIDENCE_INVALID` | Tệp minh chứng sai loại (chỉ PNG, JPG, PDF) hoặc quá 5 MB |
| 422 | `PARAMETER_INVALID` | Giá trị tham số ngoài khoảng cho phép, thời điểm hiệu lực ở quá khứ, hoặc vi phạm ràng buộc chéo (vd `capacity_warn` ≥ `capacity`) |
| 500 | `SERVER_ERROR` | Lỗi phía máy chủ |

### 2.5. Phân trang

Danh sách dùng `limit` (mặc định 20, tối đa 100) và `offset`. Phản hồi luôn có `total` để Frontend hiện "Đang hiện X/Y" và nút "Tải thêm" (FRD F02-S05).

### 2.6. Bảng mã

| Nhóm | Giá trị |
|---|---|
| `role` | `SPECIALIST`, `MANAGER` |
| `risk_level` | `HIGH`, `MEDIUM`, `LOW` |
| `status` | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED` (BRD 6.4) |
| `outcome` | `HAS_ISSUE`, `NO_ISSUE`, `DUPLICATE` (BRD 6.5) |
| `skip_reason` | `UNREACHABLE`, `DUPLICATE`, `REFUSED`, `NOT_APPLICABLE`, `OTHER` (chờ Product Owner duyệt) |
| `method` (liên lạc) | `PHONE`, `EMAIL`, `MESSAGE` |
| `contact.result` | `REACHED`, `NO_ANSWER`, `CALLBACK`, `WRONG_NUMBER` |
| `suggested_action` | `CONTACT`, `MONITOR`, `NO_ACTION` |
| `sla_state` | `ok`, `soon` (còn dưới `soon_hours`), `over` (quá hạn), `none` (đơn đã đóng) |
| `aggregation_rule` | `max-v1` (điểm đơn = điểm product item cao nhất) |
| `data_source` (sản phẩm) | `olist_order_items`, `synthetic_v1` |
| `decision` | `NO_FURTHER_ACTION`, `FOLLOW_UP_CUSTOMER`, `WORK_WITH_SELLER`, `REFER_AFTER_SALES` (đề xuất, chờ Product Owner duyệt) |
| `preferred_language` | `vi`, `en`, `null` (chưa lưu) |
| `parameter.status` | `ACTIVE`, `SCHEDULED` (hiệu lực ở tương lai), `SUPERSEDED` (đã bị phiên bản sau thay) |
| `sla_calendar` | `CALENDAR` (giờ đồng hồ), `BUSINESS_HOURS` (giờ làm việc) |
| `event_type` | `CLAIM`, `ASSIGN`, `REASSIGN`, `STATUS`, `CONTACT`, `SKIP`, `REOPEN`, `OVERRIDE`, `MODEL_NOTE`, `COMMENT`, `DECISION`, `PARAMETER_CHANGE` |

## 3. Đối tượng dữ liệu

### 3.1. Order (case đơn rủi ro)

Dùng chung cho danh sách, chi tiết và kết quả các thao tác. Chỉ chứa field biết được trước mốc dự báo.
Đơn là đơn vị workflow (nhận, giao, liên lạc, trạng thái); sản phẩm là đơn vị ML (FRD 4.1).

| Field | Kiểu | Ý nghĩa | Nguồn |
|---|---|---|---|
| `order_id` | string(32) | Mã đơn Olist | Olist |
| `case_id` | string | Mã case xử lý (`app.review_cases`) | Backend |
| `risk_score` | number 0–1 | Điểm tổng hợp của đơn, không ai sửa được | Model + aggregation |
| `risk_level` | enum | Mức rủi ro của điểm tổng hợp theo threshold | Model + threshold |
| `aggregation_rule` | string | Quy tắc tổng hợp từ điểm sản phẩm, có version (`max-v1`) | Model |
| `top_factors` | string[] | Yếu tố liên quan của sản phẩm có điểm cao nhất, có thể rỗng | Model |
| `suggested_action` | enum | Đề xuất cho đơn, chỉ tham khảo | Model |
| `model_version`, `predicted_at`, `threshold_version` | string | Metadata của lần dự báo (FRD F04-S02) | Model |
| `items_count` | int | Số sản phẩm trong đơn | Backend |
| `top_item` | object | Sản phẩm cần kiểm tra trước: `product_item_id`, `category`, `risk_score`, `risk_level`, `synthetic_data_flag` (FRD F02-S02) | Backend |
| `has_synthetic_item` | bool | Đơn có ít nhất một sản phẩm dữ liệu giả lập | Backend |
| `items` | Item[] | Chỉ có trong `GET /orders/{id}`: mọi sản phẩm, xếp score giảm dần (mục 3.2) | Model |
| `seller_id`, `category`, `customer_city`, `customer_state` | string | Bối cảnh đơn | Olist |
| `order_value`, `freight` | number (R$) | Giá trị đơn, phí ship | Olist |
| `purchase_at`, `approved_at`, `carrier_at`, `delivered_at`, `estimated_at` | datetime | Mốc giao hàng (backend giả chỉ có ngày) | Olist |
| `cycle_no` | int | Chu kỳ xử lý hiện tại, bắt đầu từ 1, tăng mỗi lần mở lại (BRD 6.8) | Backend |
| `queued_at` | datetime | Mốc bắt đầu chu kỳ hiện tại (vào queue hoặc mở lại gần nhất); tính SLA, aging | Backend |
| `original_queued_at` | datetime | Lần vào queue đầu tiên, không đổi khi mở lại | Backend |
| `status` | enum | Trạng thái xử lý | Backend |
| `self_claim_allowed` | bool | Specialist được tự nhận không (`false` với HIGH) | **Backend tính** |
| `assignee_id`, `assignee_name` | string \| null | Mã và tên người đang giữ | Backend |
| `outcome`, `skip_reason` | enum \| null | Kết quả khi COMPLETED / lý do khi SKIPPED | Backend |
| `updated_at` | datetime | Lần cập nhật gần nhất | Backend |
| `closed_at` | datetime \| null | Lúc hoàn tất hoặc bỏ qua | Backend |
| `reopen_count` | int | Số lần đã mở lại | Backend |
| `parameter_version` | string | Bộ tham số áp dụng: đang mở = bộ hiện hành; đã đóng = bộ lúc đóng (BRD 6.9 mục 3) | **Backend tính** |
| `sla_due_at` | datetime \| null | Hạn SLA của chu kỳ hiện tại (null khi đã đóng) | **Backend tính** |
| `sla_state`, `sla_hours_left` | enum, number \| null | Còn hạn / sắp hạn / quá hạn; số giờ còn lại (âm = quá hạn) | **Backend tính** |
| `aging_hours` | number | Số giờ trong chu kỳ hiện tại | **Backend tính** |
| `total_aging_hours` | number | Số giờ kể từ `original_queued_at` | **Backend tính** |
| `is_escalated` | bool | Nằm queue ≥ `aging_days` ngày chưa đóng | **Backend tính** |
| `is_stale`, `stale_hours` | bool, number \| null | Đang xử lý ≥ `stale_hours` không cập nhật | **Backend tính** |
| `contact_count` | int | Số lần liên lạc **trong chu kỳ hiện tại** | **Backend tính** |
| `max_contact` | int | Số lần tối đa theo bộ tham số áp dụng | **Backend tính** |
| `needs_decision` | bool | Case đã đóng mà chu kỳ này chưa có quyết định của Manager | **Backend tính** |

Ví dụ (rút gọn):

```json
{
  "order_id": "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47",
  "case_id": "case-5e21b7d0",
  "risk_score": 0.84,
  "risk_level": "HIGH",
  "aggregation_rule": "max-v1",
  "top_factors": ["Seller took 4 days to hand over to the carrier", "Seller–customer distance over 2,000 km"],
  "suggested_action": "CONTACT",
  "model_version": "hd-model v0.3 (LightGBM)",
  "predicted_at": "2018-06-04 11:00",
  "threshold_version": "thr-v1",
  "items_count": 2,
  "top_item": { "product_item_id": "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47-1", "category": "bed_bath_table", "risk_score": 0.84, "risk_level": "HIGH", "synthetic_data_flag": false },
  "has_synthetic_item": true,
  "seller_id": "4a3ca9315b744ce9f8e9374361493884",
  "category": "bed_bath_table",
  "customer_city": "Fortaleza",
  "customer_state": "CE",
  "order_value": 189,
  "freight": 38.75,
  "delivered_at": "2018-06-02",
  "cycle_no": 1,
  "queued_at": "2018-06-04 11:00",
  "original_queued_at": "2018-06-04 11:00",
  "status": "IN_PROGRESS",
  "self_claim_allowed": false,
  "assignee_id": "u2",
  "assignee_name": "Trần Thị B",
  "parameter_version": "ps-20180521-0800",
  "sla_due_at": "2018-06-04 15:00",
  "sla_state": "soon",
  "sla_hours_left": 1,
  "aging_hours": 3,
  "total_aging_hours": 3,
  "contact_count": 1,
  "max_contact": 3,
  "needs_decision": false
}
```

### 3.2. Item (output ML của một sản phẩm, FRD F04-S03)

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `product_item_id` | string | `order_id` + `-` + `order_item_id` của Olist, vd `a3f9…5c30-2` |
| `product_id` | string(32) | Mã sản phẩm Olist |
| `category` | string | Ngành hàng (mã Olist) |
| `price`, `weight_g`, `photos` | number | Thuộc tính có trước mốc dự báo, được phép hiển thị |
| `risk_score`, `risk_level` | number, enum | Output của sản phẩm, không ai sửa được |
| `top_factors` | string[] | Yếu tố liên quan, không gọi là nguyên nhân; rỗng = model chưa trả |
| `suggested_action` | enum | Đề xuất cho sản phẩm |
| `model_version`, `predicted_at` | string | Metadata |
| `synthetic_data_flag` | bool | `true` = chi tiết sản phẩm giả lập vì dữ liệu gốc thiếu; giao diện bắt buộc gắn nhãn (BRD 4.1) |
| `data_source` | enum | `olist_order_items` hoặc `synthetic_v1` |

Review Olist chỉ có ở cấp order, nên các item trong cùng order kế thừa cùng nhãn huấn luyện. `risk_score` của item là rủi ro review thấp của order trong bối cảnh item đó; API và giao diện không được mô tả score này như xác suất item gây bất mãn.

### 3.3. Contact / Attempt (một lần liên lạc append-only, BRD 6.6)

`contact_id`, `cycle_no`, `attempt_no` (đếm lại từ 1 trong mỗi chu kỳ), `contacted_at`, `method`, `result`, `note`,
`next_contact_date` (có thể null), `evidence` (mảng `{ file_id, file_name, file_type, file_size, url }`; `url` để mở lại tệp, có thể null), `evidence_ref` (mã cuộc gọi, tiêu đề email),
`created_by`, `created_by_name`.

### 3.4. Comment, Decision (BRD 6.11–6.12; FRD F08-S05/F12)

- Comment: `created_at`, `author_id`, `author_name`, `author_role`, `text`.
- Decision: `created_at`, `actor_id`, `actor_name`, `cycle_no`, `decision`, `reason`, `next_step`, `next_step_assignee_id`, `next_step_assignee_name`, `due_date` (có thể null), `note`.

### 3.5. Audit event (BRD 6.8)

`created_at`, `actor_id`, `actor_name`, `order_id` (**null** với `PARAMETER_CHANGE`), `event_type`, `old_value`, `new_value`, `reason`, kèm `order` tóm tắt
(`status`, `risk_level`, `assignee_name`, `event_count`, `has_override`; null khi không gắn đơn) để màn Audit History xếp thẻ theo trạng thái mà không phải gọi thêm.

## 4. Endpoint

### 4.1. Xác thực và tài khoản

#### `POST /auth/login`

Body: `{ "username": "nhanvien", "password": "123456" }`

200: `{ "token": "mock-token-u2", "user": { ...User } }`. Lỗi: `401 INVALID_CREDENTIALS`.

User:

```json
{
  "user_id": "u2",
  "username": "nhanvien",
  "full_name": "Trần Thị B",
  "role": "SPECIALIST",
  "preferred_language": null,
  "created_at": "2018-04-20 09:00",
  "active_count": 3,
  "capacity": 5,
  "slots_left": 2
}
```

`active_count`, `slots_left` là `null` với Manager.

#### `POST /auth/logout`: hủy token. Trả `204`.

#### `GET /me`: người đang đăng nhập (User).

#### `PATCH /me`: lưu ngôn ngữ giao diện theo tài khoản (FRD F11-S01)

Body: `{ "preferred_language": "vi" }`. 200: User. Lỗi: `422 VALIDATION_ERROR` nếu khác `vi`/`en`.

Luồng Frontend: chọn ngôn ngữ ở màn Đăng nhập thì lưu trên máy, đăng nhập xong gọi `PATCH /me`; chưa chọn mà tài khoản đã lưu thì dùng của tài khoản.

### 4.2. Cấu hình, tham số và người dùng

#### `GET /config`: bộ tham số đang hiệu lực (ai cũng gọi được)

```json
{
  "parameter_version": "ps-20180521-0800",
  "threshold_version": "thr-v1",
  "high_from": 0.7,
  "medium_from": 0.45,
  "sla_calendar": "CALENDAR",
  "sla_hours": { "HIGH": 4, "MEDIUM": 24, "LOW": 48 },
  "first_touch_hours": 2,
  "capacity": 5,
  "capacity_warn": 4,
  "max_contact": 3,
  "retry_gap_days": 1,
  "soon_hours": 2,
  "stale_hours": 24,
  "aging_days": 2,
  "reopen_review_days": 7,
  "reopen_review_times": 2,
  "server_time": "2018-06-04 14:00",
  "typical_order": { "handover_days": 1.0, "delivery_days": 9.0, "order_value": 84.9, "freight": 16.9 }
}
```

- `parameter_version`: mốc hiệu lực gần nhất của bộ tham số, để case đã đóng giữ đúng bộ đã dùng.
- `high_from`, `medium_from`: ngưỡng thuộc model release, đọc từ `ml.model_thresholds` theo `(release_version, threshold_version)`; chỉ đọc và **không** có trong `/parameters`. Các giá trị mẫu 0,70/0,45 không được ghi cứng ngoài mock data của `thr-v1`.
- `server_time`: Frontend dùng làm mặc định và giới hạn cho ô "thời điểm liên lạc", "thời điểm hiệu lực".
- `typical_order` (không bắt buộc): mức thường gặp để Chi tiết đơn so sánh (số ngày seller giao cho vận chuyển, tổng số ngày giao, giá trị đơn, phí ship).
  Số mẫu là trung vị của 80.039 đơn Olist giao đúng hạn được 3-5 sao. Backend chưa trả thì Frontend dùng đúng các số này.

#### `GET /parameters`: chỉ Manager (FRD F10-S01, S04)

```json
{
  "parameter_version": "ps-20180521-0800",
  "server_time": "2018-06-04 14:00",
  "items": [
    {
      "key": "capacity", "unit": "orders", "in_brd": true,
      "value": 5, "version": 1, "effective_at": "2018-05-01 00:00", "updated_by_name": "Phạm Văn D",
      "scheduled": [ { "key": "capacity", "version": 2, "value": 6, "old_value": 5, "effective_at": "2018-06-08 08:00", "status": "SCHEDULED", "actor_name": "Phạm Văn D", "reason": "Afternoon shift added from 8 June", "created_at": "2018-06-04 09:50" } ]
    }
  ],
  "history": [ { "key": "capacity", "version": 2, "value": 6, "old_value": 5, "effective_at": "2018-06-08 08:00", "status": "SCHEDULED", "actor_id": "u4", "actor_name": "Phạm Văn D", "reason": "...", "created_at": "2018-06-04 09:50" } ]
}
```

Danh sách `key` và đơn vị: `sla_calendar` (enum), `sla_hours_high`, `sla_hours_medium`, `sla_hours_low`, `first_touch_hours`, `soon_hours`, `stale_hours` (hours),
`capacity`, `capacity_warn` (orders), `max_contact`, `reopen_review_times` (times), `retry_gap_days`, `aging_days`, `reopen_review_days` (days).
`in_brd: false` = BRD 6.7 có quy tắc nhưng F10-S02 chưa liệt kê là được sửa (mục 7, điểm 7).

#### `POST /parameters`: tạo phiên bản mới, chỉ Manager (FRD F10-S02, S03)

Body: `{ "key": "capacity", "value": 6, "effective_at": "2018-06-08 08:00", "reason": "Afternoon shift added from 8 June" }`

201: phiên bản vừa tạo (dạng một dòng `history`). Tạo audit `PARAMETER_CHANGE` (`order_id = null`).

Luật Backend phải kiểm tra:

- `effective_at` bắt buộc, không ở quá khứ; `reason` bắt buộc (`422 REASON_REQUIRED`).
- Giá trị: số nguyên trong khoảng (hours 1–720, days 1–60, orders 1–20, times 1–10); `sla_calendar` chỉ `CALENDAR`/`BUSINESS_HOURS` (`422 PARAMETER_INVALID`).
- Ràng buộc chéo tại thời điểm hiệu lực: `capacity_warn < capacity`.
- Không sửa, không xóa phiên bản cũ. Phiên bản có hiệu lực = phiên bản mới nhất có `effective_at ≤ now`.
- Case đang mở dùng giá trị mới từ `effective_at`; case đã đóng giữ bộ tham số lúc đóng; số liệu đã phát sinh không bị ghi đè (BRD 6.9 mục 3–4).

#### `GET /users?role=SPECIALIST`: danh sách User kèm số đơn đang giữ (hộp thoại Assign, bộ lọc). 200: `{ "items": [User] }`.

### 4.3. Risk Queue (FRD F02, F03)

#### `GET /orders`

| Query | Ý nghĩa |
|---|---|
| `q` | Tiền tố mã đơn (0-9, a-f), **hoặc** đúng một Product Item ID (`<order_id>-<n>`) → trả đơn chứa sản phẩm đó, kèm `matched_item_id` |
| `level` | `HIGH` / `MEDIUM` / `LOW` (mức tổng hợp của đơn) |
| `status` | Mã trạng thái, hoặc `OPEN` = Pending + In progress (mặc định của màn Risk Queue) |
| `smin`, `smax` | Khoảng risk score |
| `from`, `to` | Khoảng ngày bắt đầu chu kỳ hiện tại |
| `assignee` | `me`, `none` (chưa ai nhận) hoặc mã người dùng |
| `seller`, `category` | Mã seller, mã ngành hàng |
| `outcome` | `O:<outcome>` (đơn hoàn tất) hoặc `S:<skip_reason>` (đơn bỏ qua) |
| `sla` | `over`, `soon`, `esc` (escalated), `stale` |
| `needs_decision` | `true` = chỉ case cần Manager quyết định (trang Decisions) |
| `sort` | Bỏ trống = ưu tiên (score ↓ → SLA gần hạn → nằm queue lâu, BRD 6.2); `sla`; `aging` |
| `limit`, `offset` | Phân trang |

Các điều kiện kết hợp AND. Một đơn luôn chỉ một dòng (FRD F02-S02). 200: `{ "items": [Order], "total": 16, "limit": 8, "offset": 0 }`. Lỗi: `400 INVALID_ORDER_ID`.

#### `GET /orders/summary`: số liệu cho banner Risk Queue (FRD F02-S01)

```json
{
  "high_pending": 3,
  "high_pending_overdue": 1,
  "overdue": 8,
  "escalated": 3,
  "stale": 2,
  "needs_decision": 5,
  "first_pending": { "...": "(Order)" },
  "me": { "...": "(User)" }
}
```

`first_pending` = đơn Pending đứng đầu thứ tự ưu tiên **mà người gọi được phép nhận**: với Specialist là đơn LOW/MEDIUM đầu tiên, với Manager là đơn đầu tiên bất kỳ; `null` nếu không có.

#### `GET /orders/filter-options`: `{ "sellers": [...], "categories": [...] }`

### 4.4. Order Detail (FRD F04)

#### `GET /orders/{order_id}`

```json
{
  "order": { "...": "(Order, có items)" },
  "cycles": [
    { "cycle_no": 1, "started_at": "2018-05-25 09:00", "ended_at": "2018-06-02 09:00", "contact_count": 1, "parameter_version": "ps-20180521-0800" },
    { "cycle_no": 2, "started_at": "2018-06-02 09:00", "ended_at": "2018-06-02 16:00", "contact_count": 1, "parameter_version": "ps-20180521-0800" }
  ],
  "contacts": [ { "...": "(Contact, mọi chu kỳ, cũ → mới)" } ],
  "comments": [ { "...": "(Comment, cũ → mới)" } ],
  "decisions": [ { "...": "(Decision, mới → cũ)" } ],
  "next_step": { "decision": "FOLLOW_UP_CUSTOMER", "reason": "Customer reported a warranty issue", "next_step": "Call back about warranty", "next_step_assignee_id": "u2", "next_step_assignee_name": "Trần Thị B", "due_date": "2018-06-06", "decided_by": "Phạm Văn D", "decided_at": "2018-06-04 14:02" },
  "status_history": [ { "created_at": "2018-05-25 10:00", "actor_name": "Trần Thị B", "event_type": "CLAIM", "old_value": "PENDING · (none)", "new_value": "IN_PROGRESS · Trần Thị B" } ],
  "model_notes": [],
  "audit_events": [ { "...": "(Audit event, mới → cũ)" } ],
  "seller_open_count": 2
}
```

- `next_step`: quyết định gần nhất của Manager; `null` nếu chưa có (Frontend tự gợi ý theo trạng thái).
- `status_history`: sự kiện `CLAIM`, `ASSIGN`, `REASSIGN`, `STATUS`, `SKIP`, `REOPEN`, `DECISION`, cũ → mới; **ai xem đơn cũng nhận** (khác `audit_events`).
- `audit_events`: **chỉ trả cho Manager**, Specialist nhận `null`.
- `model_notes`: ghi chú "cần xem lại model" của Manager, ai cũng xem được.

Lỗi: `404 ORDER_NOT_FOUND`.

### 4.5. Thao tác trên đơn

Mọi thao tác thành công đều trả Order mới nhất (`order`) để Frontend vẽ lại, và tạo audit event.

| Endpoint | Ai gọi | Body | Thành công | Lỗi |
|---|---|---|---|---|
| `POST /orders/{id}/claim` | Specialist | – | 200 `{ order, me }` | 403 `HIGH_RISK_REQUIRES_ASSIGN`, 409 `ALREADY_CLAIMED`, 409 `INVALID_STATE`, 422 `CAPACITY_FULL`, 403 |
| `POST /orders/{id}/assign` | Manager | `assignee_id`, `reason`, `override_capacity` | 200 `{ order, previous_assignee_name }` | 422 `CAPACITY_FULL`, 422 `REASON_REQUIRED`, 409, 403 |
| `POST /files` | Người đang giữ đơn | multipart/form-data, field `file` (1 tệp) | 201 `{ file_id, file_name, file_type, file_size, url }` | 422 `EVIDENCE_INVALID`, 422 `VALIDATION_ERROR` |
| `POST /orders/{id}/contacts` | Assignee hiện tại | `contacted_at`, `method`, `result`, `note`, `next_contact_date`, `evidence`, `evidence_ref` | 201 `{ contact, order }`; có thể trả order đã chuyển `SKIPPED` | 422 `MAX_CONTACTS_REACHED`, 422 `EVIDENCE_INVALID`, 422 `VALIDATION_ERROR`, 409, 403 |
| `POST /orders/{id}/complete` | Người giữ đơn, Manager | `outcome`, `note` | 200 `{ order }` | 422 `VALIDATION_ERROR`, 409, 403 |
| `POST /orders/{id}/skip` | Người giữ đơn, Manager | `reason`, `note` (bắt buộc khi `OTHER`) | 200 `{ order }` | 422 `VALIDATION_ERROR`, 409, 403 |
| `POST /orders/{id}/reopen` | Manager | `reason`, `review_confirmed` | 200 `{ order }` (về `PENDING`, chu kỳ mới) | 422 `REASON_REQUIRED`, 422 `REVIEW_CONFIRMATION_REQUIRED`, 409, 403 |
| `POST /orders/{id}/model-notes` | Manager | `note` | 201 ghi chú vừa tạo | 422 `VALIDATION_ERROR`, 403 |
| `POST /orders/{id}/comments` | Người đang giữ đơn, Manager | `text` (≤ 1.000 ký tự) | 201 Comment | 422 `VALIDATION_ERROR`, 403 |
| `POST /orders/{id}/decisions` | Manager | `decision`, `reason`, `next_step`, `next_step_assignee_id`, `due_date`, `note` | 201 `{ decision, order }` | 422 `REASON_REQUIRED`, 422 `VALIDATION_ERROR`, 403 |

Luật Backend phải kiểm tra:

- **Claim** (BRD 6.3): chỉ đơn `PENDING`, **không phải HIGH**; người gọi đang giữ dưới `capacity` đơn. Hai người bấm cùng lúc thì chỉ một người thành công: cập nhật có điều kiện theo `row_version` (khoá lạc quan).
- **Assign**: đơn chưa đóng; Manager giao được mọi mức, HIGH bắt buộc đi qua đây; reassign hoặc override bắt buộc `reason`; người nhận đủ `capacity` thì phải có `override_capacity: true` và tạo thêm audit `OVERRIDE`.
- **Contacts/Attempts**: chỉ assignee hiện tại của case `IN_PROGRESS`; tối đa `max_contact` lần trong chu kỳ; append-only, không có endpoint sửa/xóa. `contacted_at` không ở tương lai. Evidence tối đa 3 file PNG/JPG/PDF, mỗi file ≤ 5 MB; không nhận URL tùy ý. Frontend upload qua `POST /files`, rồi gửi mảng `{ file_id, file_name, file_type, file_size }`; mỗi `file_id` chỉ gắn một Attempt.
- **Auto-skip**: nếu Attempt thứ `max_contact` có kết quả khác `REACHED`, Backend nguyên tử lưu Attempt, chuyển case sang `SKIPPED`, đặt `skip_reason = UNREACHABLE`, đóng assignment/cycle và tạo audit `CONTACT` + `SKIP`. `UNREACHABLE` không phải completed outcome.
- **Reopen** (BRD 6.8): chỉ đơn `COMPLETED`/`SKIPPED`; tạo chu kỳ mới (`cycle_no + 1`, `queued_at = now`), reset bộ đếm liên lạc và SLA, giữ lịch sử liên lạc và `original_queued_at`; đóng quá `reopen_review_days` ngày hoặc đã mở lại từ `reopen_review_times` lần thì cần `review_confirmed: true`.
- **Comments**: tạo audit `COMMENT`. Không sửa/xóa.
- **Decisions**: `decision`, `reason`, `next_step` bắt buộc; `next_step_assignee_id` nếu có phải là user active; `due_date` không ở quá khứ. Decision gắn cycle hiện tại, append-only và tạo audit `DECISION`. Quyết định chỉ điều phối, không tự liên hệ, hoàn tiền hoặc bồi thường.

### 4.6. Dashboard (FRD F01) và Audit History (FRD F09)

#### `GET /dashboard`: chỉ Manager

Query: `days` (1, 3, 7; bỏ trống = mọi thời gian), `level`, `seller`, `category`, `assignee`, `status`, `product_item` (Product Item ID), `view` (`order` mặc định | `product`).
Mọi số liệu tính trên cùng một bộ lọc, cùng định nghĩa với Risk Queue (BRD mục 7).

Phản hồi gồm các khối của v0.1 (`as_of`, `from`, `totals`, `rates`, `by_level`, `score_bands`, `by_seller`, `by_category`, `workload`, `attention`, `recent_overrides`) và thêm:

```json
{
  "view": "product",
  "trend": [
    { "date": "2018-05-29", "HIGH": 0, "MEDIUM": 0, "LOW": 0 },
    { "date": "2018-06-04", "HIGH": 6, "MEDIUM": 4, "LOW": 0 }
  ],
  "product": {
    "totals": { "total_items": 26, "HIGH": 9, "MEDIUM": 11, "LOW": 6, "synthetic": 3, "orders": 21 },
    "by_category": [ { "key": "office_furniture", "total": 5, "high": 3, "open": 4, "related": [] } ],
    "top_items": [ { "product_item_id": "a3f9…5c30-1", "order_id": "a3f9…5c30", "category": "office_furniture", "risk_score": 0.91, "risk_level": "HIGH", "synthetic_data_flag": false, "order_status": "PENDING", "top_factor": "Seller took 5 days to hand over to the carrier" } ]
  }
}
```

- `trend` (F01-S08): số case vào queue theo ngày của `original_queued_at`, tách mức, theo cùng bộ lọc; `days` trống thì 7 ngày gần nhất.
- `product` chỉ có khi `view=product` (F01-S02/S03): đếm trên product item của các đơn đã lọc. `workload`, `attention`, `recent_overrides` luôn ở cấp case đơn.
- `recent_overrides`: 5 audit event gần nhất thuộc `ASSIGN`, `REASSIGN`, `REOPEN`, `OVERRIDE`, `PARAMETER_CHANGE`.
- `service`: chất lượng chăm sóc trên cùng bộ lọc.

  ```json
  { "cases": 21, "contacted": 7, "reached": 3, "with_first_contact": 7, "first_in_sla": 5,
    "median_first_contact_hours": 1, "issue_found": 1, "issue_followed_up": 1, "high_open_not_contacted": 4 }
  ```

  `contacted`/`reached`: số case có ít nhất một lần liên lạc / một lần liên lạc được (mọi chu kỳ). `first_in_sla`: lần liên lạc đầu của chu kỳ hiện tại nằm trước hạn SLA.
  `median_first_contact_hours`: trung vị giờ từ lúc vào queue tới lần liên lạc đầu (`null` nếu chưa có). `issue_followed_up`: case "Có vấn đề" đã có quyết định của Manager.
- `actions` (đề xuất 13/10): việc Manager cần làm, backend xếp theo mức ảnh hưởng tới khách. Mỗi phần tử có `code`, `severity` (`danger` | `warn` | `info`) và số liệu kèm theo; Frontend tự dựng câu theo ngôn ngữ.

  | `code` | Khi nào | Field kèm theo |
  |---|---|---|
  | `ASSIGN_HIGH` | Có đơn HIGH chưa người nhận | `count`, `overdue`, `suggest` (nhân viên còn nhiều slot nhất hoặc `null`) |
  | `REBALANCE` | Nhân viên hết slot mà có đơn quá hạn | `user_id`, `full_name`, `active`, `capacity`, `overdue`, `suggest` |
  | `STALE` | Có đơn đang xử lý quá `stale_hours` không cập nhật | `count`, `hours` |
  | `DECIDE` | Có case cần Manager quyết định | `count` |
  | `SELLER_HOTSPOT` | Seller đầu bảng có ≥ 3 đơn HIGH và ≥ 50% đơn của seller là HIGH | `seller_id`, `high`, `total`, `high_total` |

  Ngưỡng của `SELLER_HOTSPOT` đang cố định trong backend giả, cần BA chốt có đưa vào Parameter Configuration không.

Specialist gọi: `403 FORBIDDEN`.

#### `GET /audit-events`: chỉ Manager, chỉ đọc

Query: `event_type`, `actor_id`, `order_id` (bắt đầu bằng; bỏ qua event không gắn đơn), `override_only=true` (chỉ `REASSIGN`, `REOPEN`, `OVERRIDE`).

200: `{ "items": [Audit event], "total": 1, "all_total": 28 }`. `all_total` là tổng số event chưa lọc.

## 5. Truy vết FRD → endpoint

| Function FRD | Endpoint |
|---|---|
| F01 Risk Overview Dashboard | `GET /dashboard` (`view`, `trend`, `product_item`), `GET /orders/filter-options`, `GET /users` |
| F02 Risk Queue | `GET /orders`, `GET /orders/summary` |
| F03 Search and Filter | Query của `GET /orders` (`q` nhận cả Product Item ID), `GET /orders/filter-options` |
| F04 Order Detail | `GET /orders/{id}` (`items`, `cycles`, `status_history`) |
| F05 Claim and Assignment | `POST /orders/{id}/claim`, `POST /orders/{id}/assign`, `GET /users` |
| F06 Review Status and Outcome | `POST /orders/{id}/complete`, `POST /orders/{id}/skip` |
| F07 Attempt, Contact Retry and Escalation | `POST /files`, `POST /orders/{id}/contacts`; field SLA/escalation/`contact_count` trong Order |
| F08 Manager Override | `POST /orders/{id}/assign` (`override_capacity`), `POST /orders/{id}/reopen`, `POST /orders/{id}/model-notes` |
| F09 Audit History | `GET /audit-events`, `audit_events` trong `GET /orders/{id}` |
| F10 Parameter Configuration | `GET /parameters`, `POST /parameters`, `GET /config` |
| F11 Language Switch | `PATCH /me`, header `Accept-Language` |
| F08-S05 Nhận xét | `POST /orders/{id}/comments` |
| F12 Manager Decision | `POST /orders/{id}/decisions`, `GET /orders?needs_decision=true` |

## 6. Yêu cầu tích hợp Frontend với Backend thật

Khi `web/Prototype` được đưa vào repository triển khai, áp dụng các bước sau:

1. Sửa **một file** `web/Prototype/js/config.js`: `USE_MOCK: false`, `BASE_URL` = địa chỉ API, `AUTH` = `"bearer"` hoặc `"cookie"`.
   Không cần xoá thẻ `<script>` nào, không sửa trang nào. Thử nhanh không sửa file: thêm `?mock=0&api=<BASE_URL>` vào địa chỉ trang.
2. Backend bật CORS cho địa chỉ chạy Frontend nếu hai bên khác cổng (cho phép header `Authorization`, `Content-Type`, `Accept-Language`).
3. Mở `web/Prototype/html/api-check.html`: trang gọi các endpoint chỉ đọc của Backend và so cấu trúc JSON với backend giả, chỉ ra field thiếu hoặc sai kiểu.
4. Cần xem một backend "mẫu" trả lời qua HTTP: `node web/Prototype/tools/mock-backend.js` (cổng 8000, cùng luật và JSON với tài liệu này).

## 7. Điểm cần chốt

1. **Múi giờ và định dạng thời gian.** Database lưu `timestamptz`, API bản nháp trả `"YYYY-MM-DD HH:mm"` không kèm múi giờ. Cần chốt: API trả ISO 8601 hay giữ dạng gọn, hiển thị theo giờ Brazil (dữ liệu Olist) hay giờ Việt Nam.
2. **Cách đăng nhập.** Bản nháp dùng token Bearer. Nếu Backend chọn session cookie thì `api.js` bỏ header `Authorization` và bật `credentials: "include"`.
3. **Lịch SLA giờ làm việc.** `sla_calendar = BUSINESS_HOURS` cần bảng giờ làm việc, ngày lễ. Backend giả đang tính theo giờ đồng hồ cho cả hai.
4. **Contract với nhóm ML.** Output theo sản phẩm, `aggregation_rule = max-v1`, `synthetic_data_flag`, `data_source` phải khớp mục 3.1–3.2 và data dictionary; còn cần triển khai pipeline product-item và kiểm thử aggregation.
5. **Kết quả Attempt dùng để auto-skip.** v0.5 chốt mọi `result != REACHED`, gồm cả `CALLBACK`, ở Attempt cuối là điều kiện tự chuyển `SKIPPED/UNREACHABLE`. Manager có thể reopen nếu cần thêm chu kỳ liên hệ.
6. **Danh mục quyết định và retention policy cho minh chứng**: quyền và giới hạn upload đã chốt trong BRD/FRD; danh mục quyết định và thời hạn lưu tệp vẫn cần Product Owner/nhóm vận hành duyệt.
7. **Tham số chưa có trong F10-S02** (`in_brd: false`): SLA nhận đơn, ngưỡng cảnh báo capacity, "sắp hạn", quá lâu không cập nhật, escalation, xem xét khi mở lại. Cần chốt có cho Manager sửa không.
8. **Upload minh chứng.** v0.3 đề xuất `POST /files` (mục 4.5); Frontend đã gọi theo cách này. Backend chọn nơi lưu tệp và có trả `url` để xem lại hay không.

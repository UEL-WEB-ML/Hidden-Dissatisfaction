# TÀI LIỆU API (API CONTRACT)

## Hệ thống nhận diện và ưu tiên đơn hàng có nguy cơ bất mãn ẩn

| Thuộc tính | Nội dung |
|---|---|
| Phiên bản | 0.1 |
| Trạng thái | Bản nháp, Trúc (Frontend) và Trung (Backend) cùng chốt |
| Ngày | 05/10/2026 |
| Tài liệu liên quan | BRD_olist_hidden_dissatisfaction.md (v3.0); FRD_olist_hidden_dissatisfaction.md (v1.0); DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md (v0.1, bản nháp); ERD – TBD |
| Bản chạy thử | `Prototype/js/mock-server.js` trả lời đúng mọi endpoint trong tài liệu này |

## 1. Mục đích và nguyên tắc

Tài liệu này là thỏa thuận giữa Frontend và Backend: mỗi endpoint nhận gì, trả gì, lỗi thì trả mã nào.
Hai bên làm song song theo tài liệu này. Frontend đã chạy trên backend giả (`mock-server.js`) đúng như mô tả dưới đây;
khi Backend xong, Frontend chỉ đổi `BASE_URL` trong `Prototype/js/api.js`.

Nguyên tắc:

1. **Backend là nơi kiểm tra luật nghiệp vụ** (BRD mục 6): quyền theo vai, capacity 5 đơn, tối đa 3 lần liên lạc, chuyển trạng thái hợp lệ, bắt buộc lý do. Frontend ẩn nút trái quyền cho dễ dùng, nhưng Backend vẫn kiểm tra lại mọi request (FRD mục 3).
2. **Backend tính sẵn các số phụ thuộc thời gian** (SLA, aging, escalation, stale) và số liệu Dashboard, vì bản thật phải tính theo business calendar (BRD 6.7). Frontend chỉ hiển thị.
3. **Không endpoint nào sửa được risk score, risk level hay output gốc của model** (BRD 6.1, FRD F08-S04).
4. **Mọi thao tác ghi đều tạo audit event** ở Backend; không có endpoint sửa hay xóa audit (BRD 6.8, FRD F09-S03).

Tên field và các mã (`SPECIALIST`, `PHONE`, `CONTACT`…) theo **DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md**, để Backend đọc ghi PostgreSQL không phải đổi tên qua lại. Cách lưu trữ chi tiết (bảng, khoá) thuộc data dictionary và ERD.

## 2. Quy ước chung

### 2.1. Địa chỉ và định dạng

- Base URL: `/api/v1` (máy dev: `http://localhost:8000/api/v1`).
- Request và response đều là JSON, UTF-8. Tên field viết `snake_case`.
- Thời gian dạng `"YYYY-MM-DD HH:mm"`, ngày dạng `"YYYY-MM-DD"`, theo giờ của hệ thống (xem mục 7, điểm 1).
- Mã trạng thái, mức rủi ro, outcome… gửi bằng mã (`IN_PROGRESS`, `HAS_ISSUE`), Frontend tự đổi sang nhãn hiển thị.

### 2.2. Xác thực

- `POST /auth/login` trả `token`. Mọi request khác gửi header `Authorization: Bearer <token>`.
- Thiếu token hoặc token hết hạn: `401 UNAUTHENTICATED`, Frontend đưa người dùng về màn Đăng nhập.
- Vai (`SPECIALIST` | `MANAGER`) gắn với tài khoản, người dùng không tự chọn.

### 2.3. Lỗi

Mọi lỗi có cùng một dạng:

```json
{ "error": { "code": "CAPACITY_FULL", "message": "You already hold 5 orders. Complete or skip one to claim more.", "details": null } }
```

`message` là câu hiển thị thẳng cho người dùng (tiếng Anh, khớp ngôn ngữ giao diện). `details` có thể chứa `field` (ô nhập bị lỗi) hoặc dữ liệu thêm.

| HTTP | `code` | Khi nào |
|---|---|---|
| 400 | `INVALID_ORDER_ID` | Order ID tìm kiếm có ký tự ngoài 0-9, a-f hoặc dài quá 32 |
| 401 | `INVALID_CREDENTIALS` | Sai tên đăng nhập hoặc mật khẩu |
| 401 | `UNAUTHENTICATED` | Thiếu token hoặc token hết hạn |
| 403 | `FORBIDDEN` | Vai không được làm thao tác này (vd Specialist gọi `/dashboard`) |
| 404 | `ORDER_NOT_FOUND` | Không có đơn với mã này |
| 409 | `ALREADY_CLAIMED` | Hai người cùng nhận một đơn, người sau nhận lỗi này (FRD F05-S03) |
| 409 | `INVALID_STATE` | Chuyển trạng thái không hợp lệ (vd hoàn tất đơn đang Pending) |
| 422 | `VALIDATION_ERROR` | Thiếu hoặc sai dữ liệu bắt buộc |
| 422 | `REASON_REQUIRED` | Reassign, override, mở lại mà không có lý do |
| 422 | `CAPACITY_FULL` | Người nhận đã giữ đủ 5 đơn (BRD 6.3) |
| 422 | `MAX_CONTACTS_REACHED` | Đã đủ 3 lần liên lạc (BRD 6.6) |
| 422 | `OUTCOME_NOT_ALLOWED` | Chọn outcome "Không liên lạc được" khi chưa đủ 3 lần |
| 422 | `REVIEW_CONFIRMATION_REQUIRED` | Mở lại case quá 7 ngày hoặc đã mở lại 2 lần mà chưa xác nhận review (BRD 6.7) |
| 500 | `SERVER_ERROR` | Lỗi phía máy chủ |

### 2.4. Phân trang

Danh sách dùng `limit` (mặc định 20, tối đa 100) và `offset`. Phản hồi luôn có `total` để Frontend hiện "Showing X of Y" và nút "Load more" (FRD F02-S05).

### 2.5. Bảng mã

| Nhóm | Giá trị |
|---|---|
| `role` | `SPECIALIST`, `MANAGER` |
| `risk_level` | `HIGH`, `MEDIUM`, `LOW` |
| `status` | `PENDING`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED` (BRD 6.4) |
| `outcome` | `HAS_ISSUE`, `NO_ISSUE`, `UNREACHABLE`, `DUPLICATE` (BRD 6.5) |
| `skip_reason` | `UNREACHABLE`, `DUPLICATE`, `REFUSED`, `NOT_APPLICABLE`, `OTHER` (chờ Product Owner duyệt) |
| `method` (liên lạc) | `PHONE`, `EMAIL`, `MESSAGE` |
| `contact.result` | `REACHED`, `NO_ANSWER`, `CALLBACK`, `WRONG_NUMBER` |
| `suggested_action` | `CONTACT`, `MONITOR`, `NO_ACTION` |
| `sla_state` | `ok`, `soon` (còn dưới 2 giờ), `over` (quá hạn), `none` (đơn đã đóng) |
| `event_type` | `CLAIM`, `ASSIGN`, `REASSIGN`, `STATUS`, `CONTACT`, `SKIP`, `REOPEN`, `OVERRIDE`, `MODEL_NOTE` |

## 3. Đối tượng dữ liệu

### 3.1. Order (đơn rủi ro)

Dùng chung cho danh sách, chi tiết và kết quả các thao tác. Chỉ chứa field biết được trước mốc dự báo (BRD mục 7).

| Field | Kiểu | Ý nghĩa | Nguồn |
|---|---|---|---|
| `order_id` | string(32) | Mã đơn Olist | Olist |
| `case_id` | string | Mã case xử lý của đơn (`app.review_cases`). Một đơn có thể có nhiều case nếu bị đưa lại vào queue; endpoint `/orders/{order_id}` luôn làm việc với case đang mở hoặc case mới nhất | Backend |
| `risk_score` | number 0–1 | Điểm rủi ro, không ai sửa được | Model |
| `risk_level` | enum | Mức rủi ro theo threshold | Model + threshold |
| `top_factors` | string[] | Yếu tố liên quan đến score, có thể rỗng | Model |
| `suggested_action` | enum | Đề xuất, chỉ tham khảo | Model |
| `model_version`, `predicted_at`, `threshold_version` | string | Metadata của lần dự báo (FRD F04-S02) | Model |
| `seller_id`, `category`, `customer_city`, `customer_state` | string | Bối cảnh đơn | Olist |
| `order_value`, `freight` | number (R$) | Giá trị đơn, phí ship | Olist |
| `purchase_at`, `approved_at`, `carrier_at`, `delivered_at`, `estimated_at` | datetime | Mốc giao hàng (backend giả chỉ có ngày) | Olist |
| `queued_at` | datetime | Lúc vào Risk Queue (tính aging, SLA) | Backend |
| `status` | enum | Trạng thái xử lý | Backend |
| `assignee_id`, `assignee_name` | string \| null | Mã và tên người đang giữ | Backend |
| `outcome`, `skip_reason` | enum \| null | Kết quả khi COMPLETED / lý do khi SKIPPED | Backend |
| `updated_at` | datetime | Lần cập nhật gần nhất | Backend |
| `closed_at` | datetime \| null | Lúc hoàn tất hoặc bỏ qua | Backend |
| `reopen_count` | int | Số lần đã mở lại | Backend |
| `sla_due_at` | datetime \| null | Hạn SLA (null khi đã đóng) | **Backend tính** |
| `sla_state`, `sla_hours_left` | enum, number \| null | Còn hạn / sắp hạn / quá hạn; số giờ còn lại (âm = quá hạn) | **Backend tính** |
| `aging_hours` | number | Số giờ nằm trong queue | **Backend tính** |
| `is_escalated` | bool | Nằm queue ≥ 2 ngày chưa đóng | **Backend tính** |
| `is_stale`, `stale_hours` | bool, number \| null | Đang xử lý ≥ 1 ngày không cập nhật | **Backend tính** |
| `contact_count` | int | Số lần đã liên lạc | **Backend tính** |

Ví dụ:

```json
{
  "order_id": "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47",
  "risk_score": 0.84,
  "risk_level": "HIGH",
  "top_factors": [
    "Seller took 4 days to hand over to the carrier",
    "Seller–customer distance over 2,000 km",
    "Shipping fee higher than 70% of orders"
  ],
  "seller_id": "4a3ca9315b744ce9f8e9374361493884",
  "category": "bed_bath_table",
  "customer_city": "Fortaleza",
  "customer_state": "CE",
  "order_value": 189,
  "freight": 38.75,
  "purchase_at": "2018-05-15",
  "approved_at": "2018-05-15",
  "carrier_at": "2018-05-19",
  "delivered_at": "2018-06-02",
  "estimated_at": "2018-06-14",
  "queued_at": "2018-06-04 11:00",
  "status": "IN_PROGRESS",
  "updated_at": "2018-06-04 14:03",
  "model_version": "hd-model v0.3 (LightGBM)",
  "predicted_at": "2018-06-04 11:00",
  "reopen_count": 0,
  "case_id": "case-5e21b7d0",
  "assignee_id": "u2",
  "assignee_name": "Trần Thị B",
  "closed_at": null,
  "threshold_version": "thr-v1",
  "suggested_action": "CONTACT",
  "outcome": null,
  "skip_reason": null,
  "sla_due_at": "2018-06-04 15:00",
  "sla_state": "soon",
  "sla_hours_left": 0.93,
  "aging_hours": 3.07,
  "is_escalated": false,
  "is_stale": false,
  "stale_hours": 0.02,
  "contact_count": 2
}
```

### 3.2. Contact (một lần liên lạc, BRD 6.6)

`contact_id`, `attempt_no` (1–3), `contacted_at`, `method`, `result`, `note`, `next_contact_date` (ngày hẹn liên lạc lại, có thể null), `created_by`, `created_by_name`.

### 3.3. Audit event (BRD 6.8)

`created_at`, `actor_id`, `actor_name`, `order_id`, `event_type`, `old_value`, `new_value`, `reason`, kèm `order` tóm tắt
(`status`, `risk_level`, `assignee_name`, `event_count`, `has_override`) để màn Audit History xếp thẻ theo trạng thái mà không phải gọi thêm.

## 4. Endpoint

### 4.1. Xác thực

#### `POST /auth/login`

Body: `{ "username": "nhanvien", "password": "123456" }`

200: ```json
{
  "token": "mock-token-u2",
  "user": {
    "user_id": "u2",
    "full_name": "Trần Thị B",
    "role": "SPECIALIST",
    "active_count": 3,
    "capacity": 5,
    "slots_left": 2
  }
}
```

Lỗi: `401` ```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Incorrect username or password.",
    "details": null
  }
}
```

#### `POST /auth/logout`: hủy token. Trả `204`.

#### `GET /me`: người đang đăng nhập và số đơn đang giữ

```json
{
  "user_id": "u2",
  "full_name": "Trần Thị B",
  "role": "SPECIALIST",
  "active_count": 3,
  "capacity": 5,
  "slots_left": 2
}
```

`active_count`, `slots_left` là `null` với Manager.

### 4.2. Cấu hình và người dùng

#### `GET /config`: ngưỡng nghiệp vụ đang áp dụng (BRD 6.7, initial configuration có version)

```json
{
  "version": "cfg-v1 (effective 2018-05-01, owner: Product Owner)",
  "threshold_version": "thr-v1",
  "high_from": 0.7,
  "medium_from": 0.45,
  "capacity": 5,
  "capacity_warn": 4,
  "max_contact": 3,
  "retry_gap_days": 1,
  "sla_hours": {
    "HIGH": 4,
    "MEDIUM": 24,
    "LOW": 48
  },
  "soon_hours": 2,
  "stale_hours": 24,
  "aging_days": 2,
  "reopen_review_days": 7,
  "reopen_review_times": 2,
  "server_time": "2018-06-04 14:00"
}
```

`server_time` là giờ của máy chủ; Frontend dùng nó làm giá trị mặc định và giới hạn cho ô "thời điểm liên lạc".

#### `GET /users?role=SPECIALIST`: danh sách người dùng kèm số đơn đang giữ (hộp thoại Assign, bộ lọc)

```json
{
  "items": [
    {
      "user_id": "u1",
      "full_name": "Nguyễn Văn A",
      "role": "SPECIALIST",
      "active_count": 1,
      "capacity": 5,
      "slots_left": 4
    },
    {
      "user_id": "u2",
      "full_name": "Trần Thị B",
      "role": "SPECIALIST",
      "active_count": 3,
      "capacity": 5,
      "slots_left": 2
    },
    {
      "user_id": "u3",
      "full_name": "Lê Văn C",
      "role": "SPECIALIST",
      "active_count": 5,
      "capacity": 5,
      "slots_left": 0
    }
  ]
}
```

### 4.3. Risk Queue (FRD F02, F03)

#### `GET /orders`

| Query | Ý nghĩa |
|---|---|
| `q` | Order ID bắt đầu bằng chuỗi này (0-9, a-f) |
| `level` | `HIGH` / `MEDIUM` / `LOW` |
| `status` | Mã trạng thái, hoặc `OPEN` = Pending + In progress (mặc định của màn Risk Queue) |
| `smin`, `smax` | Khoảng risk score |
| `from`, `to` | Khoảng ngày vào queue |
| `assignee` | `me`, `none` (chưa ai nhận) hoặc mã người dùng |
| `seller`, `category` | Mã seller, mã ngành hàng |
| `outcome` | `O:<outcome>` (đơn hoàn tất) hoặc `S:<skip_reason>` (đơn bỏ qua) |
| `sla` | `over`, `soon`, `esc` (escalated), `stale` |
| `sort` | Bỏ trống = ưu tiên (score ↓ → SLA gần hạn → nằm queue lâu, BRD 6.2); `sla`; `aging` |
| `limit`, `offset` | Phân trang |

Các điều kiện kết hợp AND. 200:

```json
{
  "items": [
    {
      "...": "(Order object, mục 3.1)"
    }
  ],
  "total": 7,
  "limit": 1,
  "offset": 0
}
```

Lỗi: `400 INVALID_ORDER_ID`.

#### `GET /orders/summary`: số liệu cho banner Risk Queue (FRD F02-S01)

```json
{
  "high_pending": 3,
  "high_pending_overdue": 1,
  "overdue": 8,
  "escalated": 3,
  "stale": 2,
  "first_pending": {
    "...": "(Order object, mục 3.1)"
  },
  "me": {
    "user_id": "u2",
    "full_name": "Trần Thị B",
    "role": "SPECIALIST",
    "active_count": 3,
    "capacity": 5,
    "slots_left": 2
  }
}
```

`first_pending` là đơn Pending đứng đầu thứ tự ưu tiên ("Start with"), `null` nếu không còn đơn chờ.

#### `GET /orders/filter-options`: giá trị cho ô lọc seller, ngành hàng

```json
{
  "sellers": [
    "7c67e1448b00f6e969d365cea6b010ab",
    "4a3ca9315b744ce9f8e9374361493884",
    "..."
  ],
  "categories": [
    "bed_bath_table",
    "computers_accessories",
    "furniture_decor",
    "..."
  ]
}
```

### 4.4. Order Detail (FRD F04)

#### `GET /orders/{order_id}`

```json
{
  "order": {
    "...": "(Order object, mục 3.1)"
  },
  "contacts": [
    {
      "contact_id": "5e21b7d0-1",
      "attempt_no": 1,
      "contacted_at": "2018-06-04 11:30",
      "method": "PHONE",
      "result": "NO_ANSWER",
      "note": "Called twice, no answer",
      "next_contact_date": "2018-06-05",
      "created_by": "u2",
      "created_by_name": "Trần Thị B"
    }
  ],
  "model_notes": [],
  "audit_events": [
    {
      "created_at": "2018-06-04 11:30",
      "actor_id": "u2",
      "actor_name": "Trần Thị B",
      "order_id": "5e21b7d09a4c4f8e8b3d2a6c1f0e9d47",
      "event_type": "CONTACT",
      "old_value": "0/3",
      "new_value": "1/3 · No answer",
      "reason": "",
      "order": {
        "status": "IN_PROGRESS",
        "risk_level": "HIGH",
        "assignee_name": "Trần Thị B",
        "event_count": 2,
        "has_override": false
      }
    }
  ],
  "seller_open_count": 2
}
```

- `model_notes`: ghi chú "cần xem lại model" của Manager, ai cũng xem được.
- `audit_events`: lịch sử của đơn, mới nhất trước; **chỉ trả cho Manager**, Specialist nhận `null`.
- `seller_open_count`: số đơn khác của cùng seller còn đang mở.

Lỗi: `404 ORDER_NOT_FOUND`.

### 4.5. Thao tác trên đơn

Mọi thao tác thành công đều trả Order mới nhất (`order`) để Frontend vẽ lại, và tạo audit event.

| Endpoint | Ai gọi | Body | Thành công | Lỗi |
|---|---|---|---|---|
| `POST /orders/{id}/claim` | Specialist | – | 200 `{ order, me }` | 409 `ALREADY_CLAIMED`, 409 `INVALID_STATE`, 422 `CAPACITY_FULL`, 403 |
| `POST /orders/{id}/assign` | Manager | `assignee_id`, `reason`, `override_capacity` | 200 `{ order, previous_assignee_name }` | 422 `CAPACITY_FULL`, 422 `REASON_REQUIRED`, 409, 403 |
| `POST /orders/{id}/contacts` | Người đang giữ đơn | `contacted_at`, `method`, `result`, `note`, `next_contact_date` | 201 `{ contact, order }` | 422 `MAX_CONTACTS_REACHED`, 422 `VALIDATION_ERROR`, 409, 403 |
| `POST /orders/{id}/complete` | Người giữ đơn, Manager | `outcome`, `note` | 200 `{ order }` | 422 `VALIDATION_ERROR`, 422 `OUTCOME_NOT_ALLOWED`, 409, 403 |
| `POST /orders/{id}/skip` | Người giữ đơn, Manager | `reason`, `note` (bắt buộc khi `OTHER`) | 200 `{ order }` | 422 `VALIDATION_ERROR`, 409, 403 |
| `POST /orders/{id}/reopen` | Manager | `reason`, `review_confirmed` | 200 `{ order }` (về `PENDING`, không người giữ) | 422 `REASON_REQUIRED`, 422 `REVIEW_CONFIRMATION_REQUIRED`, 409, 403 |
| `POST /orders/{id}/model-notes` | Manager | `note` | 201 ghi chú vừa tạo | 422 `VALIDATION_ERROR`, 403 |

Luật Backend phải kiểm tra:

- **Claim** (BRD 6.3): chỉ đơn `PENDING`; người gọi đang giữ dưới 5 đơn. Hai người bấm cùng lúc thì chỉ một người thành công: Backend cập nhật có điều kiện theo `row_version` (khoá lạc quan, xem data dictionary) để không bao giờ có hai người cùng giữ một đơn.
- **Assign**: đơn chưa đóng; reassign (đơn đã có người giữ) hoặc override bắt buộc `reason`; người nhận đủ 5 đơn thì phải có `override_capacity: true` và tạo thêm audit `OVERRIDE`.
- **Contacts**: chỉ người đang giữ đơn; tối đa `max_contact` lần (hiện là 3); `contacted_at` không ở tương lai.
- **Complete**: `outcome = UNREACHABLE` chỉ hợp lệ khi đã đủ 3 lần liên lạc.
- **Reopen**: chỉ đơn `COMPLETED`/`SKIPPED`; đóng quá 7 ngày hoặc đã mở lại từ 2 lần thì cần `review_confirmed: true`.

Ví dụ claim thành công:

```json
{
  "order": {
    "...": "(Order object)"
  },
  "me": {
    "user_id": "u2",
    "full_name": "Trần Thị B",
    "role": "SPECIALIST",
    "active_count": 4,
    "capacity": 5,
    "slots_left": 1
  }
}
```

Ví dụ hai người cùng claim: `409` ```json
{
  "error": {
    "code": "ALREADY_CLAIMED",
    "message": "Order 7f3e2a1b… was just claimed by Nguyễn Văn A.",
    "details": {
      "assignee_name": "Nguyễn Văn A"
    }
  }
}
```

Ví dụ Specialist đã đủ 5 đơn: `422` ```json
{
  "error": {
    "code": "CAPACITY_FULL",
    "message": "You already hold 5 orders. Complete or skip one to claim more.",
    "details": null
  }
}
```

Ví dụ Manager giao cho người đã đủ 5 đơn mà không override: `422` ```json
{
  "error": {
    "code": "CAPACITY_FULL",
    "message": "Lê Văn C already holds 5 orders. Tick \"Override capacity\" and enter a reason.",
    "details": null
  }
}
```

Ví dụ ghi liên lạc khi đã đủ 3 lần: `422` ```json
{
  "error": {
    "code": "MAX_CONTACTS_REACHED",
    "message": "All 3 contact attempts are used; attempt 4 is not allowed.",
    "details": null
  }
}
```

### 4.6. Dashboard (FRD F01) và Audit History (FRD F09)

#### `GET /dashboard`: chỉ Manager

Query: `days` (1, 3, 7; bỏ trống = mọi thời gian), `level`, `seller`, `category`, `assignee`, `status`.
Mọi số liệu tính trên cùng một bộ lọc, cùng định nghĩa với Risk Queue (BRD mục 8). Ví dụ (mỗi danh sách cắt còn 1 phần tử):

```json
{
  "as_of": "2018-06-04 14:04",
  "from": "2018-05-29",
  "totals": {
    "total": 19,
    "PENDING": 5,
    "IN_PROGRESS": 11,
    "COMPLETED": 2,
    "SKIPPED": 1,
    "high_pending": 1,
    "high_pending_overdue": 0,
    "overdue": 8,
    "stale": 2
  },
  "rates": {
    "closed": 3,
    "completed": 2,
    "skipped": 1,
    "unreachable": 0,
    "issue_found": 1
  },
  "by_level": [
    {
      "level": "HIGH",
      "count": 7
    },
    {
      "level": "MEDIUM",
      "count": 8
    },
    {
      "level": "LOW",
      "count": 4
    }
  ],
  "score_bands": [
    {
      "min": 0.8,
      "max": 1,
      "count": 3,
      "open": 3
    },
    {
      "min": 0.6,
      "max": 0.8,
      "count": 8,
      "open": 8
    },
    {
      "min": 0.4,
      "max": 0.6,
      "count": 5,
      "open": 3
    },
    {
      "min": 0.2,
      "max": 0.4,
      "count": 2,
      "open": 1
    },
    {
      "min": 0,
      "max": 0.2,
      "count": 1,
      "open": 1
    }
  ],
  "by_seller": [
    {
      "key": "7c67e1448b00f6e969d365cea6b010ab",
      "total": 6,
      "high": 4,
      "open": 6,
      "related": [
        "office_furniture",
        "watches_gifts",
        "furniture_decor",
        "sports_leisure"
      ]
    }
  ],
  "by_category": [
    {
      "key": "office_furniture",
      "total": 3,
      "high": 2,
      "open": 3,
      "related": [
        "7c67e1448b00f6e969d365cea6b010ab"
      ]
    }
  ],
  "workload": [
    {
      "user_id": "u1",
      "full_name": "Nguyễn Văn A",
      "active_count": 2,
      "capacity": 5,
      "slots_left": 3,
      "overdue": 0,
      "stale": 0,
      "completed": 2,
      "has_data": true
    }
  ],
  "attention": [
    {
      "order": {
        "...": "(Order object)"
      },
      "reasons": [
        {
          "code": "SLA_OVERDUE"
        }
      ]
    }
  ],
  "recent_overrides": [
    {
      "created_at": "2018-06-04 09:35",
      "actor_id": "u4",
      "actor_name": "Phạm Văn D",
      "order_id": "6a7b8c9d0e1f4a2b3c4d5e6f7a8b9c0d",
      "event_type": "ASSIGN",
      "old_value": "PENDING · (none)",
      "new_value": "IN_PROGRESS · Lê Văn C",
      "reason": "",
      "order": {
        "status": "IN_PROGRESS",
        "risk_level": "HIGH",
        "assignee_name": "Lê Văn C",
        "event_count": 1,
        "has_override": false
      }
    }
  ]
}
```

- `from`: ngày bắt đầu của bộ lọc thời gian; Frontend gắn vào link drill-down sang Risk Queue (FRD F01-S06).
- `by_seller`, `by_category`: xếp theo số đơn HIGH, rồi số đơn mở; `related` là ngành hàng của seller (hoặc seller của ngành hàng).
- `attention.reasons[].code`: `SLA_OVERDUE`, `ESCALATED` (kèm `hours`), `STALE` (kèm `hours`, `assignee_name`).
- `recent_overrides`: 5 audit event gần nhất thuộc loại `ASSIGN`, `REASSIGN`, `REOPEN`, `OVERRIDE`.

Specialist gọi: `403` ```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Only managers can do this.",
    "details": null
  }
}
```

#### `GET /audit-events`: chỉ Manager, chỉ đọc

Query: `event_type`, `actor_id`, `order_id` (bắt đầu bằng), `override_only=true` (chỉ `REASSIGN`, `REOPEN`, `OVERRIDE`).

```json
{
  "items": [
    {
      "created_at": "2018-06-04 09:20",
      "actor_id": "u4",
      "actor_name": "Phạm Văn D",
      "order_id": "8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f",
      "event_type": "REASSIGN",
      "old_value": "Trần Thị B",
      "new_value": "Lê Văn C",
      "reason": "B is off this afternoon; C knows customers in the North region",
      "order": {
        "status": "IN_PROGRESS",
        "risk_level": "HIGH",
        "assignee_name": "Lê Văn C",
        "event_count": 2,
        "has_override": true
      }
    }
  ],
  "total": 1,
  "all_total": 28
}
```

`all_total` là tổng số event chưa lọc, để hiện "X of Y events".

## 5. Truy vết FRD → endpoint

| Function FRD | Endpoint |
|---|---|
| F01 Risk Overview Dashboard | `GET /dashboard`, `GET /orders/filter-options`, `GET /users` |
| F02 Risk Queue | `GET /orders`, `GET /orders/summary` |
| F03 Search and Filter | Query của `GET /orders`, `GET /orders/filter-options` |
| F04 Order Detail | `GET /orders/{id}` |
| F05 Claim and Assignment | `POST /orders/{id}/claim`, `POST /orders/{id}/assign`, `GET /users` |
| F06 Review Status and Outcome | `POST /orders/{id}/complete`, `POST /orders/{id}/skip` |
| F07 Contact Retry and Escalation | `POST /orders/{id}/contacts`; field SLA/escalation trong Order |
| F08 Manager Override | `POST /orders/{id}/assign` (`override_capacity`), `POST /orders/{id}/reopen`, `POST /orders/{id}/model-notes` |
| F09 Audit History | `GET /audit-events`, `audit_events` trong `GET /orders/{id}` |

## 6. Cách Frontend chuyển sang Backend thật

1. Trong 5 file `Prototype/html/*.html`, bỏ 2 dòng nạp `mock-data.js` và `mock-server.js`.
2. Sửa `BASE_URL` trong `Prototype/js/api.js`. `api.js` tự chuyển sang `fetch` khi không còn backend giả.
3. Backend bật CORS cho địa chỉ chạy Frontend nếu hai bên khác cổng.

## 7. Điểm cần chốt giữa Frontend và Backend

1. **Múi giờ và định dạng thời gian.** Database lưu `timestamptz` (có múi giờ) theo data dictionary, nhưng API bản nháp trả `"YYYY-MM-DD HH:mm"` không kèm múi giờ cho gọn. Cần chốt: API trả ISO 8601 (`2018-06-04T14:00:00-03:00`) hay giữ dạng gọn, và hiển thị theo giờ Brazil (dữ liệu Olist) hay giờ Việt Nam. Đổi sang ISO thì Frontend chỉ sửa hàm đọc giờ trong `common.js`.
2. **Cách đăng nhập.** Bản nháp dùng token Bearer. Nếu Backend chọn session cookie thì `api.js` bỏ header `Authorization` và bật `credentials: "include"`.
3. **Business calendar.** SLA và "1 ngày làm việc" cần lịch làm việc, ngày lễ. Backend giả đang tính theo giờ đồng hồ.
4. **Model output vào hệ thống thế nào.** Contract với nhóm ML (Huy nạp vào bảng predictions) quyết định các field `risk_*`, `top_factors`, `model_version`; cần khớp với mục 3.1.
5. **Outcome "Không liên lạc được" và luật "sau lần 3 chuyển SKIPPED" chồng nhau** (BRD 6.5 và 6.6, đã ghi ở README Prototype). Hiện API cho cả hai cách.
6. **Biểu đồ risk orders theo thời gian** (BRD 3.2) chưa có trong FRD F01, nên `/dashboard` chưa trả. Nếu thêm thì bổ sung field `trend: [{ date, HIGH, MEDIUM, LOW }]`.

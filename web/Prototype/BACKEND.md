# Nối backend vào frontend

Frontend chỉ lấy và ghi dữ liệu qua `js/api.js`, đúng theo **API contract v0.3** (repo `docs`, `docs/API_CONTRACT_olist_hidden_dissatisfaction.md`).
Backend làm đúng contract là chạy, không phải sửa trang nào.

## 1. Chuyển sang backend thật: sửa 1 file

`js/config.js`:

```js
var HD_CONFIG = {
  BASE_URL: "http://localhost:8000/api/v1",   // địa chỉ API của bạn
  USE_MOCK: false,                            // false = gọi BASE_URL; true = backend giả trong trình duyệt
  AUTH: "bearer"                              // "bearer" (token) hoặc "cookie" (session cookie)
};
```

- Không cần xoá thẻ `<script>` của `mock-data.js` / `mock-server.js`: `USE_MOCK: false` thì hai file đó không chạy.
- Thử nhanh không sửa file: mở `html/login.html?mock=0&api=http://localhost:8000/api/v1`. Trình duyệt nhớ lựa chọn này;
  `?mock=1` quay về backend giả, `?mock=default` theo lại `config.js`.
- Khi `USE_MOCK: false`, frontend tự ẩn ghi chú vàng, khung công cụ demo và danh sách tài khoản thử.

## 2. Backend cần làm gì để frontend chạy

| Việc | Chi tiết |
|---|---|
| Endpoint | 24 endpoint trong contract mục 4 (frontend gọi đủ, không gọi gì ngoài danh sách đó) |
| Lỗi | Luôn trả `{ "error": { "code", "message", "details" } }` (contract 2.4). Frontend hiện thẳng `message`, nên viết câu cho người dùng đọc, theo header `Accept-Language` |
| Đăng nhập | `POST /auth/login` → `{ token, user }`. Kiểu cookie: chỉ cần `{ user }` + đặt cookie. Hết phiên trả `401`, frontend tự về trang đăng nhập |
| CORS | Nếu frontend và API khác cổng: cho phép origin của frontend, header `Authorization, Content-Type, Accept-Language`, method `GET, POST, PATCH, OPTIONS`. Kiểu cookie thêm `Access-Control-Allow-Credentials: true` |
| Thời gian | Trả `"YYYY-MM-DD HH:mm"` hoặc ISO 8601 có múi giờ đều được. Frontend gửi lên dạng `"YYYY-MM-DD HH:mm"` |
| Upload minh chứng | `POST /files` (multipart, field `file`) → `201 { file_id, file_name, file_type, file_size, url }`. Sau đó frontend gửi `evidence: [{ file_id, ... }]` trong `POST /orders/{id}/contacts` |
| Số tính sẵn | SLA, aging, escalation, stale, số liệu dashboard: backend tính (contract mục 1, nguyên tắc 3), frontend chỉ hiển thị |

## 3. Tự kiểm tra

1. **So cấu trúc JSON:** mở `html/api-check.html`, điền `BASE_URL` và một tài khoản Manager, bấm "Chạy kiểm tra".
   Trang gọi 15 lượt chỉ đọc (kể cả lỗi 400/401/404) và so với backend giả: đỏ là field frontend cần mà backend thiếu, vàng là sai kiểu.
2. **Xem một backend mẫu trả lời qua HTTP:** `node tools/mock-backend.js` (Node 18+, không cần cài gói).
   Chạy ở `http://localhost:8000/api/v1`, cùng luật và cùng JSON với contract; thử bằng curl/Postman để so với API của bạn:
   ```
   curl -s -X POST localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"quanly","password":"123456"}'
   curl -s localhost:8000/api/v1/orders?limit=2 -H "Authorization: Bearer mock-token-u4"
   ```
   Server này cũng phục vụ luôn frontend: `http://localhost:8000/html/login.html?mock=0&api=/api/v1`.
3. **Bấm thử các luồng chính:** đăng nhập Specialist nhận đơn → ghi liên lạc kèm tệp → hoàn tất; Manager giao đơn HIGH, ghi quyết định, mở lại case, đổi tham số.

## 4. Tài khoản mẫu (chỉ có trong backend giả)

Mật khẩu đều là `123456`: `nhanvien`, `nhanvien2`, `nhanvien3` (Specialist), `quanly` (Manager). Chi tiết ở `README.md`.

## 5. Bản đồ code

| File | Vai trò |
|---|---|
| `js/config.js` | Cấu hình duy nhất cần sửa |
| `js/api.js` | Mỗi hàm = 1 endpoint của contract; gọi API bằng AJAX (`XMLHttpRequest`); gửi token/cookie, `Accept-Language`, đổi lỗi HTTP thành `ApiError` |
| `js/common.js` | Dùng chung: nạp `GET /me` + `GET /config`, nhãn song ngữ, định dạng thời gian, thanh điều hướng |
| `js/mock-data.js`, `js/mock-server.js` | Backend giả (dùng khi `USE_MOCK: true`, và là bản mẫu cho `tools/mock-backend.js`) |
| `html/*.html` | Mỗi trang 1 file, chỉ gọi `api.xxx()` |
| `html/api-check.html` | Trang tự kiểm tra API (không nằm trong menu) |
| `tools/mock-backend.js` | Backend giả chạy qua HTTP |

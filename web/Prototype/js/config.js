// =========================================================
// config.js — CHỖ DUY NHẤT cần sửa khi nối backend thật
// Các trang và api.js đọc từ đây, không phải sửa file nào khác.
// Hướng dẫn nối backend: BACKEND.md
// =========================================================

var HD_CONFIG = {
  // Địa chỉ API thật (API_CONTRACT mục 2.1)
  BASE_URL: "http://localhost:8000/api/v1",

  // true: dùng backend giả chạy trong trình duyệt (mock-server.js). false: gọi BASE_URL bằng fetch.
  // Để false thì mock-data.js / mock-server.js vẫn được nạp nhưng không chạy, không cần xoá thẻ <script>.
  USE_MOCK: true,

  // Cách đăng nhập (API_CONTRACT mục 7 điểm 2)
  //   "bearer": POST /auth/login trả token, các request sau gửi header Authorization: Bearer <token>
  //   "cookie": backend đặt session cookie, frontend gửi kèm cookie (credentials: "include"), không dùng token
  AUTH: "bearer"
};

// Đổi nhanh khi thử mà không sửa file (máy nào đổi máy đó nhớ, lưu trong localStorage):
//   ?mock=0                               -> gọi backend thật
//   ?mock=0&api=http://localhost:8000/api/v1   -> gọi backend thật ở địa chỉ khác
//   ?mock=1                               -> quay lại backend giả
//   ?mock=default                         -> bỏ hết phần đổi nhanh, theo đúng giá trị trong file này
(function () {
  var KEY = "hd-config-override";
  var o = {};
  try { o = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { o = {}; }
  var q = new URLSearchParams(location.search);
  if (q.get("mock") == "default") o = {};
  else {
    if (q.get("mock") == "0" || q.get("mock") == "1") o.USE_MOCK = q.get("mock") == "1";
    if (q.get("api")) o.BASE_URL = q.get("api").replace(/\/+$/, "");
    if (q.get("auth") == "bearer" || q.get("auth") == "cookie") o.AUTH = q.get("auth");
  }
  try { Object.keys(o).length ? localStorage.setItem(KEY, JSON.stringify(o)) : localStorage.removeItem(KEY); } catch (e) { }
  for (var k in o) HD_CONFIG[k] = o[k];
})();

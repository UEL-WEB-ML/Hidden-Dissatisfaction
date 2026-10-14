// =========================================================
// api.js — NƠI DUY NHẤT frontend lấy và ghi dữ liệu
// Mỗi hàm ứng với một endpoint trong API_CONTRACT_olist_hidden_dissatisfaction.md (v0.2). Các trang chỉ gọi api.xxx(), không đọc dữ liệu ở đâu khác.
//
// Đang dùng backend giả (mock-server.js) nếu trang có nạp file đó.
// Khi backend thật chạy: bỏ 2 dòng <script> mock-data.js, mock-server.js trong các trang
// và sửa BASE_URL bên dưới. Không phải sửa trang nào khác.
// =========================================================

var API_CONFIG = {
  BASE_URL: "http://localhost:8000/api/v1",
  USE_MOCK: typeof MockServer != "undefined"
};

var TOKEN_KEY = "hd-token";
function getToken() { try { return localStorage.getItem(TOKEN_KEY); } catch (e) { return null; } }
function setToken(t) { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch (e) { } }
// Ngôn ngữ giao diện đang chọn: gửi kèm mọi request (Accept-Language) để backend trả câu lỗi đúng ngôn ngữ (FRD F11-S02)
function currentLang() { try { return localStorage.getItem("hd-lang") == "vi" ? "vi" : "en"; } catch (e) { return "en"; } }

// Lỗi trả về từ API: status là mã HTTP, code là mã lỗi trong API_CONTRACT mục 2.3
function ApiError(status, code, message, details) {
  this.status = status;
  this.code = code;
  this.message = message;
  this.details = details || null;
}

function queryString(q) {
  var p = new URLSearchParams();
  for (var k in q) if (q[k] != null && q[k] !== "") p.set(k, q[k]);
  var s = p.toString();
  return s ? "?" + s : "";
}

async function request(method, path, opts) {
  opts = opts || {};
  var query = {};
  for (var k in (opts.query || {})) if (opts.query[k] != null && opts.query[k] !== "") query[k] = String(opts.query[k]);
  var res;
  if (API_CONFIG.USE_MOCK) {
    res = await MockServer.handle(method, path, query, opts.body, getToken(), currentLang());
  } else {
    var headers = { "Accept": "application/json", "Accept-Language": currentLang() };
    if (opts.body) headers["Content-Type"] = "application/json";
    if (getToken()) headers["Authorization"] = "Bearer " + getToken();
    try {
      var r = await fetch(API_CONFIG.BASE_URL + path + queryString(query), {
        method: method, headers: headers, body: opts.body ? JSON.stringify(opts.body) : undefined
      });
      res = { status: r.status, body: r.status == 204 ? null : await r.json().catch(function () { return null; }) };
    } catch (e) {
      throw new ApiError(0, "NETWORK_ERROR", currentLang() == "vi" ? "Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại." : "Can't reach the server. Check your connection and try again.");
    }
  }
  if (res.status >= 400) {
    var err = (res.body && res.body.error) || {};
    if (res.status == 401 && path != "/auth/login") onUnauthenticated();
    throw new ApiError(res.status, err.code || "HTTP_" + res.status, err.message || "Request failed (" + res.status + ").", err.details);
  }
  return res.body;
}

// Hết phiên đăng nhập → về màn Đăng nhập
function onUnauthenticated() {
  setToken(null);
  if (!/login\.html$/.test(location.pathname)) location.href = "login.html";
}

var api = {
  // 4.1 Xác thực
  login: async function (username, password) {
    var r = await request("POST", "/auth/login", { body: { username: username, password: password } });
    setToken(r.token);
    return r.user;
  },
  logout: async function () {
    try { await request("POST", "/auth/logout"); } catch (e) { }
    setToken(null);
  },
  getMe: function () { return request("GET", "/me"); },
  updateMe: function (changes) { return request("PATCH", "/me", { body: changes }); },

  // 4.2 Cấu hình, tham số và người dùng
  getConfig: function () { return request("GET", "/config"); },
  listParameters: function () { return request("GET", "/parameters"); },
  changeParameter: function (key, value, effectiveAt, reason) {
    return request("POST", "/parameters", { body: { key: key, value: value, effective_at: effectiveAt, reason: reason } });
  },
  listUsers: function (role) { return request("GET", "/users", { query: { role: role } }); },

  // 4.3 Risk Queue
  listOrders: function (filters) { return request("GET", "/orders", { query: filters }); },
  getQueueSummary: function () { return request("GET", "/orders/summary"); },
  getFilterOptions: function () { return request("GET", "/orders/filter-options"); },

  // 4.4 Order Detail
  getOrder: function (id) { return request("GET", "/orders/" + id); },

  // 4.5 Thao tác trên đơn
  claim: function (id) { return request("POST", "/orders/" + id + "/claim"); },
  assign: function (id, assigneeId, reason, overrideCapacity) {
    return request("POST", "/orders/" + id + "/assign", { body: { assignee_id: assigneeId, reason: reason, override_capacity: !!overrideCapacity } });
  },
  addContact: function (id, contact) { return request("POST", "/orders/" + id + "/contacts", { body: contact }); },
  complete: function (id, outcome, note) { return request("POST", "/orders/" + id + "/complete", { body: { outcome: outcome, note: note } }); },
  skip: function (id, reason, note) { return request("POST", "/orders/" + id + "/skip", { body: { reason: reason, note: note } }); },
  reopen: function (id, reason, reviewConfirmed) {
    return request("POST", "/orders/" + id + "/reopen", { body: { reason: reason, review_confirmed: !!reviewConfirmed } });
  },
  addModelNote: function (id, note) { return request("POST", "/orders/" + id + "/model-notes", { body: { note: note } }); },
  addComment: function (id, text) { return request("POST", "/orders/" + id + "/comments", { body: { text: text } }); },
  addDecision: function (id, d) { return request("POST", "/orders/" + id + "/decisions", { body: d }); },

  // 4.6 Dashboard và Audit
  getDashboard: function (filters) { return request("GET", "/dashboard", { query: filters }); },
  listAuditEvents: function (filters) { return request("GET", "/audit-events", { query: filters }); }
};

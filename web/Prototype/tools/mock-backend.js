// =========================================================
// tools/mock-backend.js — backend giả chạy qua HTTP thật (Node.js, không cần cài gói nào)
//
//   node tools/mock-backend.js            -> http://localhost:8000
//   PORT=9000 node tools/mock-backend.js  -> đổi cổng
//
// Dùng chính js/mock-data.js + js/mock-server.js (cùng luật nghiệp vụ, cùng JSON với bản chạy trong trình duyệt),
// nhưng trả lời qua HTTP như backend thật: /api/v1/..., header Authorization hoặc cookie, CORS, upload multipart.
// Để làm gì:
//   - Thử frontend ở chế độ backend thật: mở http://localhost:8000/html/login.html?mock=0&api=/api/v1
//   - Backend thật có thể so request/response của mình với bản này (curl, Postman, html/api-check.html)
// Dữ liệu chỉ nằm trong bộ nhớ, tắt server là mất.
// =========================================================
const http = require("http");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..");
const PORT = +process.env.PORT || 8000;
const PREFIX = "/api/v1";

// ---- Nạp backend giả vào một "trình duyệt" tối thiểu (chỉ cần localStorage) ----
const store = new Map();
const sandbox = {
  console, setTimeout, clearTimeout, Date, JSON, Math,
  localStorage: {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  },
};
vm.createContext(sandbox);
for (const f of ["js/mock-data.js", "js/mock-server.js"]) {
  vm.runInContext(fs.readFileSync(path.join(ROOT, f), "utf8") + "\nthis.MOCK_DB = typeof MOCK_DB != 'undefined' ? MOCK_DB : this.MOCK_DB;\nthis.MockServer = typeof MockServer != 'undefined' ? MockServer : this.MockServer;", sandbox, { filename: f });
}
const MockServer = sandbox.MockServer;

// ---- Tiện ích ----
function cors(req, res) {
  const origin = req.headers.origin;
  if (origin) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Vary", "Origin");
  }
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, Accept-Language");
}
function send(res, status, body, extraHeaders) {
  const h = Object.assign({ "Content-Type": "application/json; charset=utf-8" }, extraHeaders || {});
  res.writeHead(status, h);
  res.end(body == null ? "" : JSON.stringify(body));
}
function readBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
  });
}
function cookieToken(req) {
  const m = (req.headers.cookie || "").match(/(?:^|;\s*)hd_session=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}
// multipart/form-data: chỉ cần tên tệp, loại, dung lượng của field "file"
function parseMultipart(buf, contentType) {
  const b = (contentType.match(/boundary=(?:"([^"]+)"|([^;]+))/) || [])[1] || (contentType.match(/boundary=([^;]+)/) || [])[1];
  if (!b) return {};
  const sep = Buffer.from("--" + b);
  let start = buf.indexOf(sep);
  while (start != -1) {
    const next = buf.indexOf(sep, start + sep.length);
    if (next == -1) break;
    const part = buf.subarray(start + sep.length + 2, next - 2);   // bỏ \r\n đầu và cuối
    const headEnd = part.indexOf("\r\n\r\n");
    const head = part.subarray(0, headEnd).toString("utf8");
    if (/name="file"/.test(head)) {
      return {
        file_name: (head.match(/filename="([^"]*)"/) || [])[1] || "",
        file_type: ((head.match(/Content-Type:\s*([^\r\n]+)/i) || [])[1] || "").trim(),
        file_size: part.length - headEnd - 4,
      };
    }
    start = next;
  }
  return {};
}
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".md": "text/markdown" };

// ---- Server ----
http.createServer(async (req, res) => {
  cors(req, res);
  if (req.method == "OPTIONS") { res.writeHead(204); res.end(); return; }
  const url = new URL(req.url, "http://x");

  if (!url.pathname.startsWith(PREFIX + "/")) {   // phục vụ luôn frontend để chạy cùng địa chỉ (khỏi lo CORS)
    let file = path.join(ROOT, decodeURIComponent(url.pathname == "/" ? "/html/login.html" : url.pathname));
    if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { send(res, 404, { error: { code: "NOT_FOUND", message: "Not found", details: null } }); return; }
    res.writeHead(200, { "Content-Type": (MIME[path.extname(file)] || "application/octet-stream") + "; charset=utf-8" });
    fs.createReadStream(file).pipe(res);
    return;
  }

  const apiPath = url.pathname.substring(PREFIX.length);
  const query = Object.fromEntries(url.searchParams);
  const raw = await readBody(req);
  const ctype = req.headers["content-type"] || "";
  let body = {};
  if (/multipart\/form-data/.test(ctype)) body = parseMultipart(raw, ctype);
  else if (raw.length) { try { body = JSON.parse(raw.toString("utf8")); } catch (e) { send(res, 400, { error: { code: "INVALID_JSON", message: "Body is not valid JSON.", details: null } }); return; } }

  const auth = req.headers.authorization || "";
  const token = auth.startsWith("Bearer ") ? auth.substring(7) : cookieToken(req);
  const lang = /^vi/i.test(req.headers["accept-language"] || "") ? "vi" : "en";

  const r = await MockServer.handle(req.method, apiPath, query, body, token, lang);
  const headers = {};
  if (apiPath == "/auth/login" && r.status == 200) headers["Set-Cookie"] = "hd_session=" + encodeURIComponent(r.body.token) + "; Path=/; HttpOnly; SameSite=Lax";
  if (apiPath == "/auth/logout") headers["Set-Cookie"] = "hd_session=; Path=/; Max-Age=0";
  console.log(new Date().toISOString().substring(11, 19), req.method, url.pathname + url.search, "->", r.status);
  send(res, r.status, r.status == 204 ? null : r.body, headers);
}).listen(PORT, () => {
  console.log("Backend giả: http://localhost:" + PORT + PREFIX);
  console.log("Frontend nối vào backend này: http://localhost:" + PORT + "/html/login.html?mock=0&api=" + PREFIX);
});

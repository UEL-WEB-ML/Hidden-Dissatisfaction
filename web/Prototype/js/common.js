// =========================================================
// common.js — hàm dùng chung cho mọi màn
// Gồm: ngôn ngữ giao diện (Việt/Anh), nạp người dùng + cấu hình từ API, nhãn giao diện, định dạng,
// hộp thoại, thanh điều hướng + menu avatar.
// Dữ liệu lấy qua js/api.js. Luật nghiệp vụ (capacity, retry, SLA...) do backend kiểm tra và tính;
// frontend chỉ hiển thị và báo lỗi backend trả về (FRD mục 3).
// =========================================================

// ---------- Ngôn ngữ giao diện (FRD F11) ----------
// L("English", "Tiếng Việt") trả câu theo ngôn ngữ đang chọn. Chỉ dịch phần hiển thị:
// mã trạng thái, score, ID, giá trị tham số và audit gốc giữ nguyên (F11-S03).
// Chữ viết sẵn trong HTML: thêm data-vi="..." (nội dung), data-vi-ph (placeholder), data-vi-title (title).
var LANG = currentLang();
function L(en, vi) { return LANG == "vi" ? vi : en; }
document.documentElement.lang = LANG;

function applyStaticI18n(root) {
  if (LANG != "vi") return;
  var r = root || document;
  var a = r.querySelectorAll("[data-vi]");
  for (var i = 0; i < a.length; i++) a[i].innerHTML = a[i].getAttribute("data-vi");
  var b = r.querySelectorAll("[data-vi-ph]");
  for (var j = 0; j < b.length; j++) b[j].setAttribute("placeholder", b[j].getAttribute("data-vi-ph"));
  var c = r.querySelectorAll("[data-vi-title]");
  for (var k = 0; k < c.length; k++) c[k].setAttribute("title", c[k].getAttribute("data-vi-title"));
}
applyStaticI18n();

// Đổi ngôn ngữ: lưu trên máy (để màn Đăng nhập dùng được) và lưu theo tài khoản nếu đã đăng nhập (F11-S01)
async function setLang(lang) {
  try { localStorage.setItem("hd-lang", lang); } catch (e) { }
  if (ME) { try { await api.updateMe({ preferred_language: lang }); } catch (e) { } }
  location.reload();
}
function langSwitch(cls) {
  return '<span class="lang-switch' + (cls ? " " + cls : "") + '" role="group" aria-label="' + L("Interface language", "Ngôn ngữ giao diện") + '">'
    + '<button type="button" lang="vi" aria-pressed="' + (LANG == "vi") + '" onclick="setLang(\'vi\')">VI</button>'
    + '<button type="button" lang="en" aria-pressed="' + (LANG == "en") + '" onclick="setLang(\'en\')">EN</button></span>';
}

// ---------- Người đang đăng nhập + cấu hình (nạp một lần khi mở trang) ----------
var ME = null;        // GET /me
var config = null;    // GET /config (bộ tham số đang hiệu lực: capacity, max_contact, sla_hours...)
var NOW = null;       // giờ của máy chủ, lấy từ GET /config

// Gọi đầu mỗi trang: nạp người dùng + cấu hình rồi vẽ thanh điều hướng.
// Chưa đăng nhập thì api.js tự chuyển về login.html.
async function boot(active) {
  try {
    var r = await Promise.all([api.getMe(), api.getConfig()]);
    ME = r[0]; config = r[1]; NOW = config.server_time;
  } catch (e) {
    if (e.status != 401) document.getElementById("content").innerHTML = errorHtml(L("your account", "tài khoản của bạn"));
    throw e;
  }
  // Tài khoản đã lưu ngôn ngữ khác với máy này → theo tài khoản
  if (ME.preferred_language && ME.preferred_language != LANG) {
    try { localStorage.setItem("hd-lang", ME.preferred_language); } catch (e) { }
    location.reload();
    return new Promise(function () { });
  }
  renderChrome(active);
}
// Sau mỗi thao tác: nạp lại số đơn đang giữ và giờ máy chủ
async function reloadMe() {
  var r = await Promise.all([api.getMe(), api.getConfig()]);
  ME = r[0]; config = r[1]; NOW = config.server_time;
}

// Lỗi API → { ok: false, msg } để hộp thoại hiện ngay trong form
function apiFail(e) { return { ok: false, msg: e.message || L("Something went wrong.", "Đã có lỗi xảy ra."), code: e.code }; }

// ---------- Nhãn giao diện (FRD F06-S01: nhất quán Queue/Detail/Dashboard) ----------
var STATUS_LABEL = {
  PENDING: L("Pending", "Chờ nhận"),
  IN_PROGRESS: L("In progress", "Đang xử lý"),
  COMPLETED: L("Completed", "Hoàn tất"),
  SKIPPED: L("Skipped", "Bỏ qua")
};
// Outcome khi COMPLETED (BRD 6.5). Không có UNREACHABLE: hết lượt mà không liên lạc được thì đơn tự chuyển SKIPPED (contract v0.5)
var OUTCOME_LABEL = {
  HAS_ISSUE: L("Issue found", "Có vấn đề"),
  NO_ISSUE: L("No issue", "Không có vấn đề"),
  DUPLICATE: L("Duplicate case", "Trùng case")
};
// Lý do khi SKIPPED (BRD 6.6). Danh mục chờ Product Owner duyệt.
var SKIP_LABEL = {
  UNREACHABLE: L("Unreachable after all attempts", "Không liên lạc được sau khi hết lượt"),
  DUPLICATE: L("Duplicate case", "Trùng case"),
  REFUSED: L("Customer declined to talk", "Khách từ chối trao đổi"),
  NOT_APPLICABLE: L("Order no longer applicable", "Đơn không còn cần xử lý"),
  OTHER: L("Other (note required)", "Khác (bắt buộc ghi chú)")
};
var CONTACT_RESULT_LABEL = {
  REACHED: L("Reached", "Liên lạc được"),
  NO_ANSWER: L("No answer", "Không trả lời"),
  CALLBACK: L("Asked to call back", "Hẹn gọi lại"),
  WRONG_NUMBER: L("Wrong number / address", "Sai số / sai địa chỉ")
};
var CONTACT_METHOD_LABEL = { PHONE: L("Phone", "Điện thoại"), EMAIL: "Email", MESSAGE: L("Message", "Tin nhắn") };

// Loại audit event (FRD F09-S02)
var EVENT_LABEL = {
  CLAIM: L("Claim", "Nhận đơn"),
  ASSIGN: L("Assign", "Giao đơn"),
  REASSIGN: L("Reassign", "Chuyển người"),
  STATUS: L("Status change", "Đổi trạng thái"),
  CONTACT: L("Contact attempt", "Lần liên lạc"),
  SKIP: L("Skip", "Bỏ qua"),
  REOPEN: L("Reopen", "Mở lại"),
  OVERRIDE: L("Override", "Vượt quy tắc"),
  MODEL_NOTE: L("Model note", "Ghi chú model"),
  COMMENT: L("Comment", "Nhận xét"),
  DECISION: L("Decision", "Quyết định"),
  PARAMETER_CHANGE: L("Parameter change", "Đổi tham số")
};

// Đề xuất của model (chỉ tham khảo, không tự liên hệ khách)
var ACTION_LABEL = {
  CONTACT: L("Contact customer", "Liên hệ khách"),
  MONITOR: L("Monitor; contact if capacity allows", "Theo dõi; liên hệ nếu còn slot"),
  NO_ACTION: L("No action needed", "Chưa cần làm gì")
};
// Quyết định của Manager (trang Decisions)
var DECISION_LABEL = {
  NO_FURTHER_ACTION: L("No further action", "Không cần làm thêm"),
  FOLLOW_UP_CUSTOMER: L("Follow up with the customer", "Theo dõi tiếp với khách"),
  WORK_WITH_SELLER: L("Work with the seller", "Làm việc với seller"),
  REFER_AFTER_SALES: L("Refer to after-sales team", "Chuyển bộ phận hậu mãi")
};
// Tham số vận hành (F10). Tên hiển thị + giải thích ngắn; mã (key) giữ nguyên.
var PARAM_LABEL = {
  sla_calendar: [L("SLA clock", "Cách tính SLA"), L("Calendar time counts every hour; business hours skip nights, weekends and holidays.", "Giờ đồng hồ tính mọi giờ; giờ làm việc bỏ đêm, cuối tuần, ngày lễ.")],
  sla_hours_high: [L("SLA for HIGH", "SLA mức HIGH"), L("Time to close a HIGH case after it enters the queue.", "Thời gian đóng case HIGH kể từ lúc vào queue.")],
  sla_hours_medium: [L("SLA for MEDIUM", "SLA mức MEDIUM"), L("Time to close a MEDIUM case.", "Thời gian đóng case MEDIUM.")],
  sla_hours_low: [L("SLA for LOW", "SLA mức LOW"), L("Time to close a LOW case.", "Thời gian đóng case LOW.")],
  first_touch_hours: [L("First-touch SLA", "SLA nhận đơn"), L("Warn if nobody has picked up the case by then.", "Cảnh báo nếu tới lúc này chưa ai nhận case.")],
  capacity: [L("Capacity per specialist", "Số đơn tối đa / nhân viên"), L("Most in-progress orders one specialist can hold.", "Số đơn Đang xử lý tối đa một nhân viên được giữ.")],
  capacity_warn: [L("Capacity warning at", "Cảnh báo capacity từ"), L("Show a warning from this many orders.", "Hiện cảnh báo khi giữ tới số đơn này.")],
  max_contact: [L("Contact attempts per cycle", "Số lần liên lạc / chu kỳ"), L("After the last failed attempt the case is skipped.", "Hết lượt mà vẫn không liên lạc được thì bỏ qua case.")],
  retry_gap_days: [L("Gap between attempts", "Khoảng cách giữa 2 lần"), L("Suggested days before the next attempt.", "Số ngày đề xuất trước lần liên lạc tiếp.")],
  soon_hours: [L("\"Due soon\" from", "Báo \"sắp hạn\" khi còn"), L("Mark a case due soon when this little time is left.", "Đánh dấu sắp hạn khi thời gian còn lại dưới mức này.")],
  stale_hours: [L("In-progress timeout", "Quá lâu không cập nhật"), L("Warn the manager when an in-progress case has no update for this long.", "Báo Manager khi case Đang xử lý không cập nhật quá mức này.")],
  aging_days: [L("Escalate after", "Escalation sau"), L("Cases in the queue this long move to escalation.", "Case nằm queue quá mức này được đưa vào escalation.")],
  reopen_review_days: [L("Reopen review after", "Xem xét khi mở lại sau"), L("Reopening a case closed longer than this needs a review.", "Mở lại case đã đóng lâu hơn mức này cần xác nhận xem xét.")],
  reopen_review_times: [L("Reopen review from", "Xem xét khi mở lại từ"), L("Reopening a case this many times needs a review.", "Mở lại từ số lần này cần xác nhận xem xét.")]
};
var UNIT_LABEL = { hours: L("hours", "giờ"), days: L("days", "ngày"), orders: L("orders", "đơn"), times: L("times", "lần"), "enum": "" };
var SLA_CAL_LABEL = { CALENDAR: L("Calendar time", "Giờ đồng hồ"), BUSINESS_HOURS: L("Business hours", "Giờ làm việc") };
function paramValueText(key, unit, v) {
  if (unit == "enum") return SLA_CAL_LABEL[v] || v;
  return v + " " + (UNIT_LABEL[unit] || unit);
}
function roleLabel(role) { return role == "MANAGER" ? L("Manager", "Quản lý") : L("Specialist", "Nhân viên CSKH"); }

// ---------- Thời gian ----------
var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
// Nhận cả dạng gọn của contract ("2018-06-04 14:00", "2018-06-04") lẫn ISO 8601 có múi giờ
// ("2018-06-04T14:00:00Z", "2018-06-04T14:00:00+07:00"): backend trả dạng nào cũng hiển thị đúng (API_CONTRACT mục 7 điểm 1).
// Dạng có múi giờ được đổi sang giờ của máy người xem.
function parseTime(s) {
  s = String(s);
  if (/[zZ]$|[+-]\d\d:?\d\d$/.test(s)) return new Date(s);
  var p = s.split(/[- :T.]/);
  return new Date(+p[0], +p[1] - 1, +p[2], +(p[3] || 0), +(p[4] || 0), +(p[5] || 0));
}
function pad(n) { return n < 10 ? "0" + n : "" + n; }
// Giá trị cho ô <input type="datetime-local"> / <input type="date"> từ thời gian API trả về (dạng nào cũng được)
function inputTime(s) { return fmtTime(parseTime(s)).replace(" ", "T"); }
function inputDate(s) { return fmtDate(parseTime(s)); }
// Giá trị ô datetime-local ("2018-06-04T14:00") -> dạng gửi lên API theo contract ("2018-06-04 14:00")
function apiTime(v) { return v ? v.replace("T", " ") : v; }
function fmtTime(d) {
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
}
function fmtDate(d) { return fmtTime(d).substring(0, 10); }
// EN: "Jun 4, 14:00" / "Jun 4, 2018". VI: "04/06 14:00" / "04/06/2018"
function viTime(s) {
  if (!s) return "—";
  var d = parseTime(s), hasTime = s.length > 10;
  if (LANG == "vi") return pad(d.getDate()) + "/" + pad(d.getMonth() + 1) + (hasTime ? " " + pad(d.getHours()) + ":" + pad(d.getMinutes()) : "/" + d.getFullYear());
  return MONTHS[d.getMonth()] + " " + d.getDate() + ", " + (hasTime ? pad(d.getHours()) + ":" + pad(d.getMinutes()) : d.getFullYear());
}
function shortDay(s) {             // nhãn trục ngày của biểu đồ
  var d = parseTime(s);
  return LANG == "vi" ? pad(d.getDate()) + "/" + pad(d.getMonth() + 1) : MONTHS[d.getMonth()] + " " + d.getDate();
}
function hoursBetween(a, b) { return (parseTime(b) - parseTime(a)) / 3600000; }
function daysBetween(a, b) { return Math.round((parseTime(b) - parseTime(a)) / 86400000); }
function durationText(h) {
  h = Math.abs(h);
  // Tiếng Anh gọn "45m", "5h", "3d 5h"; tiếng Việt viết đủ "45 phút", "5 giờ", "3 ngày 5 giờ" (tránh đọc "5g" thành 5 gam)
  if (h < 1) return Math.round(h * 60) + L("m", " phút");
  if (h < 24) return Math.floor(h) + L("h", " giờ");
  var d = Math.floor(h / 24), r = Math.floor(h % 24);
  return d + L("d", " ngày") + (r ? " " + r + L("h", " giờ") : "");
}
// Ngày làm việc kế tiếp (bỏ thứ Bảy, Chủ nhật). Bản thật dùng business calendar có ngày lễ.
function nextBusinessDay(s, n) {
  var d = parseTime(s);
  var added = 0;
  while (added < (n || 1)) {
    d.setDate(d.getDate() + 1);
    if (d.getDay() != 0 && d.getDay() != 6) added++;
  }
  return fmtDate(d);
}
function money(v) { return "R$ " + (LANG == "vi" ? v.toFixed(2).replace(".", ",") : v.toFixed(2)); }
function fileSize(b) { return b >= 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB"; }

// ---------- Tra cứu ----------
// Tên ngành hàng: mã Olist (bed_bath_table) → nhãn dễ đọc. Giá trị lọc vẫn dùng mã.
var CATEGORY_LABEL = {
  bed_bath_table: L("Bed, bath & table", "Giường, nhà tắm & bàn"), watches_gifts: L("Watches & gifts", "Đồng hồ & quà tặng"),
  health_beauty: L("Health & beauty", "Sức khỏe & làm đẹp"), sports_leisure: L("Sports & leisure", "Thể thao & giải trí"),
  computers_accessories: L("Computers & accessories", "Máy tính & phụ kiện"), furniture_decor: L("Furniture & decor", "Nội thất & trang trí"),
  office_furniture: L("Office furniture", "Nội thất văn phòng"), housewares: L("Housewares", "Đồ gia dụng"), toys: L("Toys", "Đồ chơi"),
  telephony: L("Telephony", "Điện thoại"), garden_tools: L("Garden tools", "Dụng cụ làm vườn")
};
function catLabel(slug) {
  if (!slug) return "";
  if (CATEGORY_LABEL[slug]) return CATEGORY_LABEL[slug];
  var t = slug.replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}
function shortId(id) { return id.substring(0, 8) + "…"; }
// Mã sản phẩm: 8 ký tự đầu của mã đơn + số thứ tự sản phẩm ("a3f9c1e2…-2")
function shortItemId(id) { var p = id.split("-"); return p[0].substring(0, 8) + "…-" + p[1]; }
function isClosed(c) { return c.status == "COMPLETED" || c.status == "SKIPPED"; }

function me() { return ME; }
function isManager() { return ME.role == "MANAGER"; }

async function logout() {
  await api.logout();
  location.href = "login.html";
}

// ---------- SLA, aging, escalation (BRD 6.7): backend tính sẵn, frontend chỉ đọc ----------
function slaDue(c) { return c.sla_due_at; }
// Trả về { code: ok | soon | over | none, text }
function slaState(c) {
  if (c.sla_state == "none" || c.sla_hours_left == null) return { code: "none", text: "—" };
  var left = c.sla_hours_left;
  return { code: c.sla_state, text: durationText(left) + (left < 0 ? L(" overdue", " quá hạn") : L(" left", " còn lại")) };
}
function agingHours(c) { return c.aging_hours; }
function isEscalated(c) { return c.is_escalated; }
function isStale(c) { return c.is_stale; }

// ---------- Nhãn HTML ----------
// Mức rủi ro: icon ô vuông viền + 3 cột sóng (HIGH tô 3 cột, MEDIUM 2, LOW 1) và chữ, không dùng nền đỏ đặc,
// để màu đỏ đặc chỉ còn một nghĩa: quá hạn SLA. Người khó phân biệt màu vẫn đọc được qua số cột + chữ.
function levelIcon(level) {
  var n = { HIGH: 3, MEDIUM: 2, LOW: 1 }[level], h = [4, 6, 8], svg = "";
  for (var i = 0; i < 3; i++) {
    svg += '<rect x="' + (4 + i * 3) + '" y="' + (12 - h[i]) + '" width="2" height="' + h[i] + '" rx="0.5" class="' + (i < n ? "on" : "off") + '"/>';
  }
  return '<svg class="lv" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">'
    + '<rect class="box" x="0.75" y="0.75" width="14.5" height="14.5" rx="3.5"/>' + svg + "</svg>";
}
function badge(level) {
  return '<span class="badge ' + level + '">' + levelIcon(level) + level + "</span>";
}
function statusBadge(status) {
  return '<span class="st ' + status + '">' + STATUS_LABEL[status] + "</span>";
}
// Nhãn "Dữ liệu giả lập" cho sản phẩm thiếu dữ liệu gốc (BRD 4.1, FRD F04-S03)
function synthTag() {
  return '<span class="synth-tag" title="' + L("Product details were simulated because the source data is missing. For testing and illustration only.",
    "Chi tiết sản phẩm được giả lập vì dữ liệu gốc thiếu. Chỉ dùng để thử nghiệm và minh họa.") + '">' + L("Simulated data", "Dữ liệu giả lập") + "</span>";
}
function slaBadge(c) {
  var s = slaState(c);
  if (s.code == "none") return '<span class="muted">—</span>';
  var label = { ok: L("On track", "Còn hạn"), soon: L("Due soon", "Sắp hạn"), over: L("Overdue", "Quá hạn") }[s.code];
  // Chấm màu + con số ("1h overdue", "45m left"). Mức nhấn theo độ gấp: quá hạn = nền đỏ nhạt chữ đỏ đậm,
  // sắp hạn = chữ vàng sẫm, còn hạn = chữ xám. Không còn cả cột khối đỏ đặc.
  return '<span class="sla ' + s.code + '" title="' + label + " · " + L("SLA due ", "Hạn SLA ") + viTime(slaDue(c)) + '"><span class="dot" aria-hidden="true"></span>' + s.text + "</span>";
}
function escBadge(c) {
  // Thẻ nhỏ viền, nằm cùng dòng với số giờ để mọi dòng trong bảng cao bằng nhau
  return isEscalated(c) ? ' <span class="esc-tag" title="' + L("In queue for " + config.aging_days + " days or more", "Nằm queue từ " + config.aging_days + " ngày trở lên") + '">' + L("Escalated", "Escalation") + "</span>" : "";
}
// Giá trị audit lưu mã (PENDING, HAS_ISSUE, NO_ANSWER…); hiển thị bằng nhãn giao diện cho dễ đọc
// Giá trị cũ → mới của audit event, dạng gọn: "PENDING · (none)" → nhãn trạng thái; "IN_PROGRESS · Trần Thị B" → nhãn + tên
function valueHtml(v) {
  if (!v) return "";
  var m = /^(PENDING|IN_PROGRESS|COMPLETED|SKIPPED)(?: · (.*))?$/.exec(v);
  if (!m) return "<b>" + humanValue(v) + "</b>";
  var rest = m[2] && m[2] != "(none)" ? ' <span class="tiny">' + humanValue(m[2]) + "</span>" : "";
  return statusBadge(m[1]) + rest;
}
function changeHtml(oldV, newV) {
  return '<span class="chg">' + (oldV ? valueHtml(oldV) + ' <span class="chg-arrow" aria-label="' + L("to", "thành") + '">' + icon("arrow") + "</span> " : "") + valueHtml(newV) + "</span>";
}
function humanValue(v) {
  if (!v) return v;
  var maps = [STATUS_LABEL, OUTCOME_LABEL, SKIP_LABEL, CONTACT_RESULT_LABEL, DECISION_LABEL];
  for (var m = 0; m < maps.length; m++) {
    for (var k in maps[m]) v = v.replace(new RegExp("\\b" + k + "\\b", "g"), maps[m][k]);
  }
  return v.replace("(none)", L("unassigned", "chưa ai nhận")).replace(/\bcycle (\d+)/, L("cycle $1", "chu kỳ $1"));
}
function outcomeText(c) {
  if (c.status == "COMPLETED") return OUTCOME_LABEL[c.outcome] || "";
  if (c.status == "SKIPPED") return SKIP_LABEL[c.skip_reason] || "";
  return "";
}
// Order ID rút gọn + nút sao chép mã đầy đủ (mã đầy đủ đọc được cả trên màn cảm ứng)
var COPY_ICON = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><rect x="5" y="5" width="9" height="9" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M3 11V3.5A1.5 1.5 0 0 1 4.5 2H11" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>';
function copyBtn(id) {
  return '<button type="button" class="copy" onclick="copyId(\'' + id + '\')" aria-label="' + L("Copy ID ", "Sao chép mã ") + id + '" title="' + L("Copy full ID", "Sao chép mã đầy đủ") + '">' + COPY_ICON + "</button>";
}
function idLink(id, href) {
  return '<a class="id" href="' + href + '" aria-label="' + L("Order ", "Đơn ") + id + '">' + shortId(id) + "</a>" + copyBtn(id);
}
// Thẻ/dòng có data-href: bấm vào chỗ trống cũng mở trang đó (link, nút, "Show all" vẫn giữ việc của chúng)
document.addEventListener("click", function (e) {
  var box = e.target.closest("[data-href]");
  if (!box || e.target.closest("a, button, summary, input, select, textarea")) return;
  if (String(window.getSelection())) return;   // đang bôi đen chữ để sao chép thì không mở
  location.href = box.getAttribute("data-href");
});
function copyId(id) {
  try { navigator.clipboard.writeText(id); } catch (e) { }
  toast(L("Copied ID ", "Đã sao chép mã ") + id);
}

// ---------- Thẻ số liệu dùng chung (Dashboard + banner Risk Queue) ----------
// Bố cục: icon + nhãn ở trên → số to → dòng phụ → link hành động ở đáy thẻ. Cả thẻ bấm được.
var ICONS = {
  clock: '<circle cx="8" cy="8" r="6"/><path d="M8 4.5V8l2.5 1.5"/>',
  up: '<path d="M2.5 11.5 6.5 7.5l2.5 2.5 4.5-5"/><path d="M10 5h3.5v3.5"/>',
  hourglass: '<path d="M4.5 2h7M4.5 14h7M5 2c0 3 6 3.5 6 6s-6 3-6 6M11 2c0 3-6 3.5-6 6s6 3 6 6"/>',
  progress: '<path d="M13.5 8A5.5 5.5 0 1 1 8 2.5"/><path d="M8 2.5h3v3"/>',
  check: '<circle cx="8" cy="8" r="6"/><path d="m5.5 8.2 1.8 1.8 3.4-3.6"/>',
  skip: '<path d="M3.5 3.5 9 8l-5.5 4.5zM12 3.5v9"/>',
  inbox: '<path d="M2.5 9.5 4 3.5h8l1.5 6v3h-11z"/><path d="M2.5 9.5h3l1 1.5h3l1-1.5h3"/>',
  target: '<circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="2.5"/>',
  gavel: '<path d="m6 3 4 4M4.5 4.5l4 4M7.5 1.5l5 5-2 2-5-5z"/><path d="M8 9l-5 5M2.5 14h6"/>',
  user: '<circle cx="8" cy="5.5" r="2.75"/><path d="M2.75 13.5c.6-2.6 2.7-4 5.25-4s4.65 1.4 5.25 4"/>',
  gear: '<circle cx="8" cy="8" r="2.2"/><path d="M8 1.5v2M8 12.5v2M1.5 8h2M12.5 8h2M3.4 3.4l1.4 1.4M11.2 11.2l1.4 1.4M3.4 12.6l1.4-1.4M11.2 4.8l1.4-1.4"/>',
  out: '<path d="M6 2.5H3.5v11H6M10 5l3 3-3 3M13 8H6"/>',
  globe: '<circle cx="8" cy="8" r="6"/><path d="M2 8h12M8 2c1.8 1.7 2.6 3.7 2.6 6S9.8 12.3 8 14C6.2 12.3 5.4 10.3 5.4 8S6.2 3.7 8 2z"/>',
  chevron: '<path d="m4.5 6.5 3.5 3.5 3.5-3.5"/>',
  clip: '<path d="M10.5 4.5 5.8 9.2a1.4 1.4 0 0 0 2 2l5-5a2.8 2.8 0 0 0-4-4l-5 5a4.2 4.2 0 0 0 6 6l4-4"/>',
  phone: '<path d="M4 2.5h2l1 3-1.5 1a8 8 0 0 0 4 4l1-1.5 3 1v2a1.5 1.5 0 0 1-1.6 1.5A11 11 0 0 1 2.5 4.1 1.5 1.5 0 0 1 4 2.5z"/>',
  users: '<circle cx="6" cy="5.5" r="2.5"/><path d="M1.5 13.5c.5-2.4 2.3-3.7 4.5-3.7s4 1.3 4.5 3.7"/><path d="M10.5 3.2a2.5 2.5 0 0 1 0 4.6M12 9.9c1.3.5 2.2 1.8 2.5 3.6"/>',
  grid: '<rect x="2" y="2" width="5" height="5" rx="1.2"/><rect x="9" y="2" width="5" height="5" rx="1.2"/><rect x="2" y="9" width="5" height="5" rx="1.2"/><rect x="9" y="9" width="5" height="5" rx="1.2"/>',
  list: '<path d="M5.5 4h8M5.5 8h8M5.5 12h8"/><circle cx="2.6" cy="4" r=".6"/><circle cx="2.6" cy="8" r=".6"/><circle cx="2.6" cy="12" r=".6"/>',
  file: '<path d="M4 1.8h5.2L12.5 5v9.2H4z"/><path d="M9 1.8V5h3.5M6.3 8.3h3.9M6.3 11h3.9"/>',
  history: '<path d="M2.6 8a5.4 5.4 0 1 0 1.6-3.8"/><path d="M2.3 2.5v2.4h2.4M8 5v3.2l2.2 1.3"/>',
  filter: '<path d="M2 3.5h12M4.5 8h7M7 12.5h2"/>',
  arrow: '<path d="M3 8h10M9 4l4 4-4 4"/>',
  store: '<path d="M2.5 6.5 3.5 2.5h9l1 4"/><path d="M2.5 6.5c0 1.1.9 2 2 2s1.8-.9 1.8-2c0 1.1.8 2 1.7 2s1.8-.9 1.8-2c0 1.1.8 2 1.8 2s1.9-.9 1.9-2"/><path d="M3.5 8.3v5.2h9V8.3M6.5 13.5v-3h3v3"/>'
};
function icon(name) {
  return '<svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' + ICONS[name] + "</svg>";
}
// o: { href, tone, icon (tên icon hoặc HTML), label, num, sub, extra, action, cls }
function kpiCard(o) {
  var ic = ICONS[o.icon] ? icon(o.icon) : o.icon;
  return '<a class="kpi tone-' + (o.tone || "neutral") + (o.cls ? " " + o.cls : "") + '" href="' + o.href + '">'
    + '<div class="kpi-head"><span class="kpi-icon">' + ic + '</span><span class="kpi-label">' + o.label + "</span></div>"
    + '<div class="kpi-num">' + o.num + "</div>"
    + (o.sub ? '<div class="kpi-sub">' + o.sub + "</div>" : "")
    + (o.extra || "")
    + (o.action ? '<div class="kpi-action">' + o.action + ' <span aria-hidden="true">→</span></div>' : "")
    + "</a>";
}
// Biểu đồ vòng: phần đã dùng / tổng (holding x/capacity). cls: "" | "warn" | "full"
function donut(value, max, cls, centerText) {
  var r = 26, len = 2 * Math.PI * r, pct = max ? Math.min(value / max, 1) : 0;
  return '<svg class="donut ' + (cls || "") + '" viewBox="0 0 64 64" width="64" height="64" role="img" aria-label="' + value + " / " + max + '">'
    + '<circle class="d-track" cx="32" cy="32" r="' + r + '"/>'
    + '<circle class="d-fill" cx="32" cy="32" r="' + r + '" stroke-dasharray="' + (len * pct).toFixed(1) + " " + len.toFixed(1) + '" transform="rotate(-90 32 32)"/>'
    + '<text x="32" y="36" text-anchor="middle">' + (centerText != null ? centerText : value + "/" + max) + "</text></svg>";
}

// ---------- Hộp thoại ----------
// Không dùng alert()/confirm() của trình duyệt. Esc để đóng, Tab không thoát ra ngoài hộp thoại,
// đóng xong trả focus về nút đã mở.
var modalOpener = null;
function openModal(title, bodyHtml, confirmText, onConfirm) {
  closeModal(true);
  modalOpener = document.activeElement;
  var m = document.createElement("div");
  m.id = "modal";
  m.className = "modal-bg";
  m.innerHTML = '<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">'
    + '<h2 id="modal-title">' + title + "</h2>"
    + '<div class="modal-body">' + bodyHtml + "</div>"
    + '<p class="form-error" id="modal-error" role="alert"></p>'
    + '<div class="modal-actions"><button class="btn" type="button" onclick="closeModal()">' + L("Cancel", "Hủy") + "</button> "
    + '<button class="btn primary" type="button" id="modal-ok">' + confirmText + "</button></div></div>";
  document.body.appendChild(m);
  m.addEventListener("mousedown", function (e) { if (e.target == m) closeModal(); });
  m.addEventListener("keydown", function (e) {
    if (e.key == "Escape") { closeModal(); return; }
    if (e.key != "Tab") return;
    var f = m.querySelectorAll("button, select, input, textarea");
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement == first) { last.focus(); e.preventDefault(); }
    else if (!e.shiftKey && document.activeElement == last) { first.focus(); e.preventDefault(); }
  });
  // onConfirm có thể trả { ok, msg } hoặc Promise (gọi API). Đang gửi thì khoá nút để không bấm hai lần.
  var okBtn = document.getElementById("modal-ok");
  okBtn.onclick = async function () {
    okBtn.disabled = true;
    var r;
    try { r = await onConfirm(); } catch (e) { r = apiFail(e); }
    okBtn.disabled = false;
    if (r && r.ok === false) {
      document.getElementById("modal-error").innerHTML = r.msg;   // lỗi hiện ngay trong hộp thoại, dữ liệu không đổi
    } else {
      closeModal();
    }
  };
  var firstField = m.querySelector(".modal-body select, .modal-body input, .modal-body textarea") || document.getElementById("modal-ok");
  firstField.focus();
}
function closeModal(silent) {
  var m = document.getElementById("modal");
  if (m) m.parentNode.removeChild(m);
  if (!silent && modalOpener && document.body.contains(modalOpener)) modalOpener.focus();
}

// Thông báo nhỏ: thành công tự tắt sau 4 giây; lỗi/cảnh báo đứng yên tới khi người dùng đóng.
function toast(msg, type) {
  type = type || "ok";
  var t = document.getElementById("toast");
  if (t == null) {
    t = document.createElement("div");
    t.id = "toast";
    document.body.appendChild(t);
  }
  t.setAttribute("role", type == "error" ? "alert" : "status");
  t.className = "toast " + type;
  t.innerHTML = '<span class="toast-msg">' + msg + '</span><button type="button" class="toast-x" aria-label="' + L("Dismiss", "Đóng") + '" onclick="hideToast()">×</button>';
  clearTimeout(window._toastTimer);
  if (type == "ok") window._toastTimer = setTimeout(hideToast, 4000);
}
function hideToast() {
  var t = document.getElementById("toast");
  if (t) t.className += " hide";
}

// Hộp thoại assign/reassign dùng chung cho Risk Queue và Order Detail. c: đơn từ API.
async function openAssign(c, onDone) {
  var list;
  try { list = (await api.listUsers("SPECIALIST")).items; } catch (e) { toast(e.message, "error"); return; }
  var opts = '<option value="">' + L("-- Choose a specialist --", "-- Chọn nhân viên --") + "</option>";
  for (var i = 0; i < list.length; i++) {
    var n = list[i].active_count;
    opts += '<option value="' + list[i].user_id + '">' + list[i].full_name + " · " + n + "/" + config.capacity
      + (n >= config.capacity ? L(" (full)", " (đã đủ)") : " · " + L(list[i].slots_left + " slot(s) left", "còn " + list[i].slots_left + " slot")) + "</option>";
  }
  var reassign = c.assignee_id != null;
  var body = '<p>' + L("Order", "Đơn") + ' <span class="id">' + shortId(c.order_id) + "</span> · " + badge(c.risk_level) + " " + c.risk_score.toFixed(2) + "</p>"
    + (c.risk_level == "HIGH" && !reassign ? '<p class="tiny">' + L("HIGH-risk orders can only reach a specialist through a manager assignment.", "Đơn HIGH chỉ tới tay nhân viên qua bước Manager giao.") + "</p>" : "")
    + (reassign ? "<p>" + L("Current assignee", "Người đang phụ trách") + ": <b>" + c.assignee_name + "</b></p>" : "")
    + '<div class="form-row"><label for="as-user">' + (reassign ? L("Move to", "Chuyển cho") : L("Assign to", "Giao cho")) + "</label><select id=\"as-user\">" + opts + "</select></div>"
    + '<div class="form-row"><label for="as-reason">' + L("Reason", "Lý do") + (reassign ? L(" (required)", " (bắt buộc)") : L(" (required if overriding)", " (bắt buộc nếu vượt capacity)")) + '</label>'
    + '<textarea id="as-reason" rows="2"></textarea></div>'
    + '<label class="check"><input type="checkbox" id="as-override"> ' + L("Override capacity: allow assigning to someone who already holds " + config.capacity + " orders",
      "Vượt capacity: cho phép giao cho người đã giữ đủ " + config.capacity + " đơn") + "</label>";
  openModal(reassign ? L("Reassign order", "Chuyển người phụ trách") : L("Assign order", "Giao đơn"), body, L("Confirm", "Xác nhận"), async function () {
    var to = document.getElementById("as-user").value;
    var reason = document.getElementById("as-reason").value.trim();
    var override = document.getElementById("as-override").checked;
    // Kiểm tra nhanh trên form cho đỡ một lượt gọi; backend vẫn kiểm tra lại
    if (!to) return { ok: false, msg: L("Choose a specialist.", "Chọn một nhân viên.") };
    if ((reassign || override) && !reason) return { ok: false, msg: L("Enter a reason: reassignments and overrides are recorded in the audit log.", "Nhập lý do: chuyển người và vượt capacity đều được ghi vào lịch sử.") };
    try {
      var r = await api.assign(c.order_id, to, reason, override);
      toast(r.previous_assignee_name
        ? L("Moved order " + shortId(c.order_id) + " from " + r.previous_assignee_name + " to " + r.order.assignee_name + ".",
          "Đã chuyển đơn " + shortId(c.order_id) + " từ " + r.previous_assignee_name + " sang " + r.order.assignee_name + ".")
        : L("Assigned order " + shortId(c.order_id) + " to " + r.order.assignee_name + ".", "Đã giao đơn " + shortId(c.order_id) + " cho " + r.order.assignee_name + "."));
      onDone();
      return { ok: true };
    } catch (e) { return apiFail(e); }
  });
}

// ---------- Trạng thái tải / lỗi (FRD F01-S02, F02-S05) ----------
// Backend giả đọc ô "Giả lập trạng thái" trong khung công cụ demo: normal | loading (chậm 2,5 giây) | error (trả 500).
function setSim(v) {
  try { localStorage.setItem("wf-sim", v); } catch (e) { }
  location.reload();
}
function skeletonHtml(rows) {
  var h = '<div class="skeleton" aria-busy="true" aria-label="' + L("Loading", "Đang tải") + '">';
  for (var i = 0; i < (rows || 4); i++) h += '<div class="sk-line" style="width:' + (92 - i * 9) + '%"></div>';
  return h + "</div>";
}
function errorHtml(what) {
  return '<div class="load-error" role="alert"><b>' + L("Couldn't load " + what + ".", "Không tải được " + what + ".") + "</b> "
    + L("Check your connection and try again.", "Kiểm tra kết nối rồi thử lại.") + ' '
    + '<button class="btn sm" type="button" onclick="location.reload()">' + L("Retry", "Thử lại") + "</button></div>";
}

// ---------- Thanh điều hướng + menu avatar ----------
// Specialist: Risk Queue · Order Detail · Contact attempts.
// Manager: Dashboard · Risk Queue · Order Detail · Decisions · Audit History · Settings.
// Order Detail luôn có trên thanh (feedback 13/10): mở đơn đang xem gần nhất, chưa xem đơn nào thì mở đơn nên làm trước.
function rememberOrder(id) { try { sessionStorage.setItem("hd-last-order", id); } catch (e) { } }
function lastOrder() { try { return sessionStorage.getItem("hd-last-order"); } catch (e) { return null; } }

function renderChrome(active) {
  renderTopbar(active);
  if (document.querySelector(".wf-tools")) return;
  renderFooter();
}
function renderTopbar(active) {
  var u = me(), last = lastOrder(), mgr = u.role == "MANAGER";
  var links = [];
  if (mgr) links.push(["overview.html", L("Dashboard", "Tổng quan"), "dashboard", "grid"]);
  links.push(["index.html", "Risk Queue", "queue", "list"]);
  links.push([last ? "order.html?id=" + last : "order.html", L("Order Detail", "Chi tiết đơn"), "detail", "file"]);
  if (!mgr) links.push(["attempt.html" + (last ? "?id=" + last : ""), L("Contact attempts", "Liên lạc khách"), "attempt", "phone"]);
  if (mgr) links.push(["decision.html", L("Decisions", "Quyết định"), "decision", "gavel"]);
  if (mgr) links.push(["audit.html", L("Audit History", "Lịch sử thao tác"), "audit", "history"]);
  if (mgr) links.push(["settings.html", L("Settings", "Cài đặt"), "settings", "gear"]);

  var html = '<span class="logo"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 16 16"><path d="M8 1.6l1.9 3.9 4.3.6-3.1 3 .7 4.3L8 11.4l-3.8 2 .7-4.3-3.1-3 4.3-.6z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M8 1.6v9.8l-3.8 2 .7-4.3-3.1-3 4.3-.6z" fill="currentColor"/></svg></span>Hidden Dissatisfaction</span>';
  html += '<span class="nav-links">';
  for (var i = 0; i < links.length; i++) {
    html += '<a href="' + links[i][0] + '"' + (links[i][2] == active ? ' class="active" aria-current="page"' : "") + ">" + icon(links[i][3]) + "<span>" + links[i][1] + "</span></a>";
  }
  html += "</span>";

  // Menu avatar (feedback 13/10): hồ sơ, ngôn ngữ, cài đặt (Manager), đăng xuất
  var parts = u.full_name.split(" "), initials = parts[0].charAt(0) + parts[parts.length - 1].charAt(0);
  html += '<span class="user">'
    + '<button type="button" class="user-btn" id="user-btn" aria-haspopup="true" aria-expanded="false" aria-controls="user-menu" onclick="toggleUserMenu()">'
    + '<span class="avatar" aria-hidden="true">' + initials + "</span>"
    + '<span class="u-text"><b>' + u.full_name + "</b><small>" + roleLabel(u.role) + "</small></span>"
    + '<span class="chev">' + icon("chevron") + "</span></button>"
    + '<div class="user-menu" id="user-menu" role="menu" hidden>'
    + '<div class="um-head"><span class="avatar lg" aria-hidden="true">' + initials + '</span><div><b>' + u.full_name + "</b><small>" + roleLabel(u.role) + " · " + u.username + "</small></div></div>"
    + (u.role == "SPECIALIST" ? '<div class="um-cap">' + L("Holding", "Đang giữ") + " <b>" + u.active_count + "/" + config.capacity + "</b> " + L("orders", "đơn") + "</div>" : "")
    + '<a role="menuitem" href="profile.html"' + (active == "profile" ? ' aria-current="page"' : "") + ">" + icon("user") + L("Profile", "Hồ sơ") + "</a>"
    + (mgr ? '<a role="menuitem" href="settings.html">' + icon("gear") + L("Parameter settings", "Cài đặt tham số") + "</a>" : "")
    + '<div class="um-lang">' + icon("globe") + "<span>" + L("Language", "Ngôn ngữ") + "</span>" + langSwitch() + "</div>"
    + '<a role="menuitem" href="login.html" class="um-out" onclick="logout(); return false;">' + icon("out") + L("Sign out", "Đăng xuất") + "</a>"
    + "</div></span>";
  document.getElementById("topbar").innerHTML = html;
}
function toggleUserMenu(open) {
  var m = document.getElementById("user-menu"), b = document.getElementById("user-btn");
  if (!m) return;
  if (open == null) open = m.hidden;
  m.hidden = !open;
  b.setAttribute("aria-expanded", open);
  if (open) { var f = m.querySelector("a, button"); if (f) f.focus(); }
}
document.addEventListener("click", function (e) {
  var m = document.getElementById("user-menu");
  if (m && !m.hidden && !e.target.closest(".user")) toggleUserMenu(false);
});
document.addEventListener("keydown", function (e) {
  var m = document.getElementById("user-menu");
  if (e.key == "Escape" && m && !m.hidden) { toggleUserMenu(false); document.getElementById("user-btn").focus(); }
});

function renderFooter() {
  // Công cụ demo: KHÔNG thuộc sản phẩm, chỉ có khi đang dùng backend giả.
  // Ẩn cùng nút "Ẩn/hiện ghi chú" để xem giao diện đúng như sản phẩm.
  if (!API_CONFIG.USE_MOCK) return;
  var u = me(), accounts = [["u2", "nhanvien", "Trần Thị B – Specialist"], ["u3", "nhanvien2", "Lê Văn C – Specialist"],
    ["u1", "nhanvien3", "Nguyễn Văn A – Specialist (VI)"], ["u4", "quanly", "Phạm Văn D – Manager"]];
  var opts = "";
  for (var j = 0; j < accounts.length; j++) {
    opts += '<option value="' + accounts[j][1] + '"' + (accounts[j][0] == u.user_id ? " selected" : "") + ">" + accounts[j][2] + "</option>";
  }
  var sim = "normal", simOpts = "";
  try { sim = localStorage.getItem("wf-sim") || "normal"; } catch (e) { }
  var sims = [["normal", "Bình thường"], ["loading", "Mạng chậm (2,5 giây)"], ["error", "Máy chủ lỗi (500)"]];
  for (var k = 0; k < sims.length; k++) simOpts += '<option value="' + sims[k][0] + '"' + (sims[k][0] == sim ? " selected" : "") + ">" + sims[k][1] + "</option>";

  var tools = document.createElement("div");
  tools.className = "wf-tools";
  tools.lang = "vi";
  tools.innerHTML = '<b>Công cụ demo prototype, không có trong sản phẩm.</b> '
    + "Đang dùng backend giả (js/mock-server.js) theo API_CONTRACT_olist_hidden_dissatisfaction.md v0.5. Bản thật: vai do tài khoản quyết định, Backend kiểm tra quyền.<br>"
    + '<label>Đăng nhập lại với: <select onchange="switchUser(this.value)">' + opts + "</select></label>"
    + ' · <label>Giả lập mạng: <select onchange="setSim(this.value)">' + simOpts + "</select></label>"
    + ' · <a href="#" onclick="resetData(); return false;">Đặt lại dữ liệu mẫu</a>'
    + " · Giờ máy chủ giả: <b>" + viTime(NOW) + "</b>";
  document.body.appendChild(tools);
}
async function switchUser(username) {
  await api.login(username, "123456");
  try { localStorage.removeItem("hd-lang"); sessionStorage.removeItem("hd-last-order"); } catch (e) { }
  location.reload();
}
function resetData() {
  MockServer.reset();
  location.reload();
}

// Màn chỉ dành cho Manager: Specialist mở thẳng địa chỉ thì báo không có quyền (backend cũng trả 403)
function requireManager() {
  if (isManager()) return true;
  document.getElementById("content").innerHTML = '<div class="alert"><span class="icon">!</span>'
    + '<a class="btn" href="index.html">' + L("Back to Risk Queue", "Về Risk Queue") + "</a>"
    + "<b>" + L("This page is for managers only.", "Trang này chỉ dành cho Manager.") + "</b><br>"
    + L("Your specialist account doesn't have access.", "Tài khoản nhân viên của bạn không có quyền xem.") + "</div>"
    + '<div class="note" lang="vi">BRD 3.1: Specialist không có Dashboard, Decisions, Settings trong MVP.</div>';
  return false;
}

// Bật/tắt các ô ghi chú màu vàng
function toggleNotes() {
  document.body.classList.toggle("hide-notes");
}

// ---------- Chế độ trình bày ----------
// Ẩn mọi thứ chỉ dành cho nhóm làm prototype (ghi chú vàng, khung công cụ demo, gợi ý tài khoản thử)
// để giao diện trông đúng như sản phẩm khi nộp bài / thuyết trình.
// Bật/tắt: nút góc dưới trái, phím ` (backtick), hoặc thêm ?present=1 / ?present=0 vào địa chỉ trang. Trạng thái được nhớ.
function setPresent(on) {
  try { localStorage.setItem("wf-present", on ? "1" : "0"); } catch (e) { }
  document.body.classList.toggle("present", on);
}
function togglePresent() {
  var on = !document.body.classList.contains("present");
  setPresent(on);
  if (on) toast("Chế độ trình bày đã bật. Nhấn phím ` (cạnh số 1) để tắt.");
}
(function initPrototypeTools() {
  // Nối backend thật (USE_MOCK = false): luôn ở chế độ sản phẩm, không hiện ghi chú, nút công cụ, tài khoản thử
  if (!API_CONFIG.USE_MOCK) { document.body.classList.add("present"); return; }
  var on = false;
  try { on = localStorage.getItem("wf-present") == "1"; } catch (e) { }
  var q = new URLSearchParams(location.search).get("present");
  if (q != null) on = q == "1";
  setPresent(on);

  var box = document.createElement("div");
  box.className = "wf-btns";
  box.lang = "vi";
  box.innerHTML = '<button type="button" class="wf-note-btn" onclick="toggleNotes()">Ghi chú: bật/tắt</button>'
    + '<button type="button" class="wf-note-btn" onclick="togglePresent()">Chế độ trình bày</button>';
  document.body.appendChild(box);

  document.addEventListener("keydown", function (e) {
    var t = e.target.tagName;
    if (e.key == "`" && t != "INPUT" && t != "TEXTAREA" && t != "SELECT") togglePresent();
  });
})();

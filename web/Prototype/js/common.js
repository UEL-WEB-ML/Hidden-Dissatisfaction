// =========================================================
// common.js — hàm dùng chung cho mọi màn
// Gồm: dữ liệu tạm, nhãn giao diện (tiếng Anh), luật nghiệp vụ (BRD mục 6), hộp thoại, thanh điều hướng.
// Prototype tự kiểm tra luật ở trình duyệt cho dễ xem; bản thật Backend vẫn kiểm tra độc lập (FRD mục 3).
// =========================================================

// ---------- Lưu tạm thao tác vào trình duyệt ----------
// Claim, complete, skip... được lưu vào localStorage để chuyển màn không mất.
// Nút "Đặt lại dữ liệu mẫu" trong khung công cụ demo xoá phần này.
var STORE_KEY = "wf-data-v2";
(function loadSaved() {
  try {
    var saved = localStorage.getItem(STORE_KEY);
    if (saved != null) {
      var d = JSON.parse(saved);
      cases = d.cases; contacts = d.contacts; audits = d.audits; NOW = d.now;
    }
  } catch (e) { /* không đọc được thì dùng dữ liệu mẫu */ }
})();

function saveData() {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify({ cases: cases, contacts: contacts, audits: audits, now: NOW }));
  } catch (e) { }
}

function resetData() {
  try { localStorage.removeItem(STORE_KEY); } catch (e) { }
  location.reload();
}

// Mỗi thao tác đẩy đồng hồ giả lên 1 phút để lịch sử có thứ tự
function tick() {
  var d = parseTime(NOW);
  d.setMinutes(d.getMinutes() + 1);
  NOW = fmtTime(d);
  return NOW;
}

// ---------- Nhãn giao diện (FRD F06-S01: nhất quán Queue/Detail/Dashboard) ----------
// Bảng thuật ngữ: giao diện dùng tiếng Anh thống nhất; mã trạng thái giữ nguyên như BRD.
var STATUS_LABEL = {
  PENDING: "Pending",
  IN_PROGRESS: "In progress",
  COMPLETED: "Completed",
  SKIPPED: "Skipped"
};

// Outcome khi COMPLETED (BRD 6.5)
var OUTCOME_LABEL = {
  HAS_ISSUE: "Issue found",
  NO_ISSUE: "No issue",
  UNREACHABLE: "Unreachable after max attempts",
  DUPLICATE: "Duplicate case"
};
// Lý do khi SKIPPED (BRD 6.6). Danh mục chờ Product Owner duyệt.
var SKIP_LABEL = {
  UNREACHABLE: "Unreachable after 3 attempts",
  DUPLICATE: "Duplicate case",
  REFUSED: "Customer declined to talk",
  NOT_APPLICABLE: "Order no longer applicable",
  OTHER: "Other (note required)"
};
var CONTACT_RESULT_LABEL = {
  REACHED: "Reached",
  NO_ANSWER: "No answer",
  CALLBACK: "Asked to call back",
  WRONG_NUMBER: "Wrong number / address"
};
var CONTACT_METHODS = ["Phone", "Email", "Message"];

// Loại audit event (FRD F09-S02)
var EVENT_LABEL = {
  CLAIM: "Claim",
  ASSIGN: "Assign",
  REASSIGN: "Reassign",
  STATUS: "Status change",
  CONTACT: "Contact attempt",
  SKIP: "Skip",
  REOPEN: "Reopen",
  OVERRIDE: "Override",
  MODEL_NOTE: "Model note"
};

// Đề xuất của model (chỉ tham khảo, không tự liên hệ khách)
var ACTION_LABEL = { HIGH: "Contact customer", MEDIUM: "Monitor; contact if capacity allows", LOW: "No action needed" };

// ---------- Thời gian ----------
var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
function parseTime(s) {            // "2018-06-04 14:00" hoặc "2018-06-04"
  var p = s.split(/[- :]/);
  return new Date(+p[0], +p[1] - 1, +p[2], +(p[3] || 0), +(p[4] || 0));
}
function pad(n) { return n < 10 ? "0" + n : "" + n; }
function fmtTime(d) {
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
}
function fmtDate(d) { return fmtTime(d).substring(0, 10); }
// "2018-06-04 14:00" → "Jun 4, 14:00"; "2018-06-04" → "Jun 4, 2018"
function viTime(s) {
  if (!s) return "—";
  var d = parseTime(s);
  return MONTHS[d.getMonth()] + " " + d.getDate() + ", " + (s.length > 10 ? pad(d.getHours()) + ":" + pad(d.getMinutes()) : d.getFullYear());
}
function hoursBetween(a, b) { return (parseTime(b) - parseTime(a)) / 3600000; }
function daysBetween(a, b) { return Math.round((parseTime(b) - parseTime(a)) / 86400000); }
function durationText(h) {
  h = Math.abs(h);
  // Dạng gọn "45m", "5h", "3d 5h" để cột Aging/SLA thẳng hàng và không xuống dòng
  if (h < 1) return Math.round(h * 60) + "m";
  if (h < 24) return Math.floor(h) + "h";
  return Math.floor(h / 24) + "d " + Math.floor(h % 24) + "h";
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

// ---------- Tra cứu ----------
function findCase(id) {
  for (var i = 0; i < cases.length; i++) if (cases[i].order_id == id) return cases[i];
  return null;
}
function findUser(id) {
  for (var i = 0; i < users.length; i++) if (users[i].id == id) return users[i];
  return null;
}
function userName(id) { var u = findUser(id); return u ? u.name : ""; }
function specialists() {
  var list = [];
  for (var i = 0; i < users.length; i++) if (users[i].role == "specialist") list.push(users[i]);
  return list;
}
// Tên ngành hàng: mã Olist (bed_bath_table) → nhãn dễ đọc (Bed, bath & table). Giá trị lọc vẫn dùng mã.
var CATEGORY_LABEL = {
  bed_bath_table: "Bed, bath & table", watches_gifts: "Watches & gifts", health_beauty: "Health & beauty",
  sports_leisure: "Sports & leisure", computers_accessories: "Computers & accessories", furniture_decor: "Furniture & decor"
};
function catLabel(slug) {
  if (!slug) return "";
  if (CATEGORY_LABEL[slug]) return CATEGORY_LABEL[slug];
  var t = slug.replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
}
function shortId(id) { return id.substring(0, 8) + "…"; }
function isClosed(c) { return c.status == "COMPLETED" || c.status == "SKIPPED"; }

function contactsOf(id) {
  var list = [];
  for (var i = 0; i < contacts.length; i++) if (contacts[i].order_id == id) list.push(contacts[i]);
  list.sort(function (a, b) { return parseTime(a.at) - parseTime(b.at); });
  return list;
}
function auditsOf(id) {
  var list = [];
  for (var i = 0; i < audits.length; i++) if (id == null || audits[i].order_id == id) list.push(audits[i]);
  list.sort(function (a, b) { return parseTime(b.at) - parseTime(a.at); });   // mới nhất lên đầu
  return list;
}

// ---------- Người đang đăng nhập ----------
// Màn Đăng nhập lưu user_id. Mở thẳng file khi chưa đăng nhập thì xem như Specialist Trần Thị B.
function me() {
  var id = null;
  try { id = localStorage.getItem("userId"); } catch (e) { }
  return findUser(id) || findUser("u2");
}
function isManager() { return me().role == "manager"; }

function logout() {
  try { localStorage.removeItem("userId"); } catch (e) { }
}

// ---------- Capacity (BRD 6.3) ----------
function activeCount(userId) {
  var n = 0;
  for (var i = 0; i < cases.length; i++) {
    if (cases[i].assignee == userId && cases[i].status == "IN_PROGRESS") n++;
  }
  return n;
}
function slotsLeft(userId) { return Math.max(0, config.capacity - activeCount(userId)); }   // slot không âm

// ---------- SLA, aging, escalation (BRD 6.7) ----------
function slaDue(c) {
  var d = parseTime(c.queued_at);
  d.setHours(d.getHours() + config.sla_hours[c.risk_level]);
  return fmtTime(d);
}
// Trả về { code: ok | soon | over | none, text }
function slaState(c) {
  if (isClosed(c)) return { code: "none", text: "—" };
  var left = hoursBetween(NOW, slaDue(c));
  if (left < 0) return { code: "over", text: durationText(left) + " overdue" };
  if (left < config.soon_hours) return { code: "soon", text: durationText(left) + " left" };
  return { code: "ok", text: durationText(left) + " left" };
}
function agingHours(c) { return hoursBetween(c.queued_at, isClosed(c) ? c.updated_at : NOW); }
// Nằm queue quá 2 ngày mà chưa đóng → escalation queue
function isEscalated(c) { return !isClosed(c) && agingHours(c) >= config.aging_days * 24; }
// IN_PROGRESS quá 1 ngày không cập nhật → cảnh báo Manager
function isStale(c) { return c.status == "IN_PROGRESS" && hoursBetween(c.updated_at, NOW) >= config.stale_hours; }

// ---------- Sắp xếp ưu tiên (BRD 6.2) ----------
// score giảm dần → gần quá SLA hơn → nằm queue lâu hơn
function byPriority(a, b) {
  if (b.risk_score != a.risk_score) return b.risk_score - a.risk_score;
  var sa = parseTime(slaDue(a)), sb = parseTime(slaDue(b));
  if (sa - sb != 0) return sa - sb;
  return parseTime(a.queued_at) - parseTime(b.queued_at);
}

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
function slaBadge(c) {
  var s = slaState(c);
  if (s.code == "none") return '<span class="muted">—</span>';
  var label = { ok: "On track", soon: "Due soon", over: "Overdue" }[s.code];
  // Chấm màu + con số ("1h overdue", "45m left"). Mức nhấn theo độ gấp: quá hạn = nền đỏ nhạt chữ đỏ đậm,
  // sắp hạn = chữ vàng sẫm, còn hạn = chữ xám. Không còn cả cột khối đỏ đặc.
  return '<span class="sla ' + s.code + '" title="' + label + " · SLA due " + viTime(slaDue(c)) + '"><span class="dot" aria-hidden="true"></span>' + s.text + "</span>";
}
function escBadge(c) {
  // Thẻ nhỏ viền, nằm cùng dòng với số giờ để mọi dòng trong bảng cao bằng nhau
  return isEscalated(c) ? ' <span class="esc-tag" title="In queue for ' + config.aging_days + ' days or more">Escalated</span>' : "";
}
// Giá trị audit lưu mã (PENDING, IN_PROGRESS…); hiển thị bằng nhãn giao diện cho dễ đọc
function humanValue(v) {
  if (!v) return v;
  for (var k in STATUS_LABEL) v = v.split(k).join(STATUS_LABEL[k]);
  return v.replace("(none)", "unassigned");
}
function outcomeText(c) {
  if (c.status == "COMPLETED") return OUTCOME_LABEL[c.outcome] || "";
  if (c.status == "SKIPPED") return SKIP_LABEL[c.skip_reason] || "";
  return "";
}
// Order ID rút gọn + nút sao chép mã đầy đủ (mã đầy đủ đọc được cả trên màn cảm ứng)
var COPY_ICON = '<svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false"><rect x="5" y="5" width="9" height="9" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M3 11V3.5A1.5 1.5 0 0 1 4.5 2H11" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>';
function copyBtn(id) {
  return '<button type="button" class="copy" onclick="copyId(\'' + id + '\')" aria-label="Copy order ID ' + id + '" title="Copy full order ID">' + COPY_ICON + "</button>";
}
function idLink(id, href) {
  return '<a class="id" href="' + href + '" aria-label="Order ' + id + '">' + shortId(id) + "</a>" + copyBtn(id);
}
function copyId(id) {
  try { navigator.clipboard.writeText(id); } catch (e) { }
  toast("Copied order ID " + id);
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
  target: '<circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="2.5"/>'
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

// ---------- Ghi audit (BRD 6.8): actor, thời gian, action, cũ, mới, lý do ----------
function addAudit(orderId, type, oldValue, newValue, reason) {
  audits.push({ at: tick(), actor: me().id, order_id: orderId, type: type, old_value: oldValue, new_value: newValue, reason: reason || "" });
}

// ---------- Thao tác nghiệp vụ ----------
// Mỗi hàm trả về { ok: true/false, msg } để màn hình hiện thông báo.

// F05-S01..S03: Specialist tự nhận
function claimCase(id) {
  var c = findCase(id), u = me();
  if (c._conflict) {   // giả lập: người khác bấm trước một nhịp
    c._conflict = false;
    c.status = "IN_PROGRESS"; c.assignee = "u1"; c.updated_at = NOW;
    audits.push({ at: NOW, actor: "u1", order_id: id, type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · Nguyễn Văn A", reason: "" });
    saveData();
    return { ok: false, msg: "Order " + shortId(id) + " was just claimed by Nguyễn Văn A. The list has been refreshed." };
  }
  if (c.status != "PENDING") return { ok: false, msg: "This order is no longer pending." };
  if (activeCount(u.id) >= config.capacity) {
    return { ok: false, msg: "You already hold " + config.capacity + " orders. Complete or skip one to claim more." };
  }
  c.status = "IN_PROGRESS"; c.assignee = u.id; c.updated_at = tick();
  addAudit(id, "CLAIM", "PENDING · (none)", "IN_PROGRESS · " + u.name);
  saveData();
  var n = activeCount(u.id);
  var msg = "Claimed order " + shortId(id) + ". You now hold " + n + "/" + config.capacity + ".";
  if (n >= config.capacity) msg += " Limit reached: complete or skip an order before claiming another.";
  else if (n >= config.capacity_warn) msg += " Almost at the limit: " + slotsLeft(u.id) + " slot left.";
  return { ok: true, msg: msg, warn: n >= config.capacity_warn };
}

// F05-S04, F05-S05, F08-S02, F08-S03: Manager assign / reassign, có thể override capacity
function assignCase(id, toUser, reason, override) {
  var c = findCase(id);
  var from = c.assignee;
  if (from == toUser) return { ok: false, msg: "That specialist is already the assignee." };
  if (activeCount(toUser) >= config.capacity) {
    if (!override) return { ok: false, msg: userName(toUser) + " already holds " + config.capacity + " orders. Tick \"Override capacity\" and enter a reason." };
    addAudit(id, "OVERRIDE", userName(toUser) + ": " + activeCount(toUser) + "/" + config.capacity + " active",
      (activeCount(toUser) + 1) + "/" + config.capacity + " (over capacity)", reason);
  }
  if (from == null) {
    c.status = "IN_PROGRESS"; c.assignee = toUser; c.updated_at = tick();
    addAudit(id, "ASSIGN", "PENDING · (none)", "IN_PROGRESS · " + userName(toUser), reason);
    saveData();
    return { ok: true, msg: "Assigned order " + shortId(id) + " to " + userName(toUser) + "." };
  }
  c.assignee = toUser; c.updated_at = tick();
  addAudit(id, "REASSIGN", userName(from), userName(toUser), reason);
  saveData();
  return { ok: true, msg: "Moved order " + shortId(id) + " from " + userName(from) + " to " + userName(toUser) + "." };
}

// F07-S01..S04: ghi nhận một lần liên lạc
function addContact(id, at, method, result, note, nextDate) {
  var c = findCase(id);
  var n = contactsOf(id).length;
  if (n >= config.max_contact) return { ok: false, msg: "All " + config.max_contact + " contact attempts are used; attempt " + (n + 1) + " is not allowed." };
  if (!at || !method || !result) return { ok: false, msg: "Time, method and result are required." };
  if (at > NOW) return { ok: false, msg: "Contact time cannot be in the future." };
  tick();
  contacts.push({ order_id: id, at: at, user: me().id, method: method, result: result, note: note, next_date: nextDate });
  c.updated_at = NOW;
  addAudit(id, "CONTACT", n + "/" + config.max_contact, (n + 1) + "/" + config.max_contact + " · " + CONTACT_RESULT_LABEL[result], "");
  saveData();
  return { ok: true, msg: "Saved contact attempt " + (n + 1) + "/" + config.max_contact + "." };
}

// F06-S02: Hoàn tất, bắt buộc outcome
function completeCase(id, outcome, note) {
  var c = findCase(id);
  if (!outcome) return { ok: false, msg: "Choose an outcome before completing." };
  if (c.status != "IN_PROGRESS") return { ok: false, msg: "Only in-progress orders can be completed." };
  c.status = "COMPLETED"; c.outcome = outcome; c.updated_at = tick();
  addAudit(id, "STATUS", "IN_PROGRESS", "COMPLETED · " + OUTCOME_LABEL[outcome], note);
  saveData();
  return { ok: true, msg: "Completed order " + shortId(id) + ". Slot released." };
}

// F06-S03: Bỏ qua, bắt buộc reason
function skipCase(id, reason, note) {
  var c = findCase(id);
  if (!reason) return { ok: false, msg: "Choose a skip reason." };
  if (reason == "OTHER" && !note) return { ok: false, msg: "\"Other\" requires a note." };
  if (c.status != "IN_PROGRESS") return { ok: false, msg: "Only in-progress orders can be skipped." };
  c.status = "SKIPPED"; c.skip_reason = reason; c.updated_at = tick();
  addAudit(id, "SKIP", "IN_PROGRESS", "SKIPPED", SKIP_LABEL[reason] + (note ? ": " + note : ""));
  saveData();
  return { ok: true, msg: "Skipped order " + shortId(id) + ". Slot released." };
}

// F08-S01: Manager mở lại, bắt buộc override reason
function reopenCase(id, reason) {
  var c = findCase(id);
  if (!reason) return { ok: false, msg: "A reason is required to reopen." };
  var old = c.status + (outcomeText(c) ? " · " + outcomeText(c) : "");
  c.status = "PENDING"; c.assignee = null; c.outcome = null; c.skip_reason = null;
  c.reopen_count++; c.queued_at = tick(); c.updated_at = NOW;
  addAudit(id, "REOPEN", old, "PENDING", reason);
  saveData();
  return { ok: true, msg: "Reopened order " + shortId(id) + "; it is back to Pending." };
}

// F08-S04: không sửa score, chỉ ghi chú model review
function addModelNote(id, note) {
  if (!note) return { ok: false, msg: "Enter a note." };
  addAudit(id, "MODEL_NOTE", "", "Flagged for model review", note);
  saveData();
  return { ok: true, msg: "Model review note saved. The original risk score is unchanged." };
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
    + '<div class="modal-actions"><button class="btn" type="button" onclick="closeModal()">Cancel</button> '
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
  document.getElementById("modal-ok").onclick = function () {
    var r = onConfirm();
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
  t.innerHTML = '<span class="toast-msg">' + msg + '</span><button type="button" class="toast-x" aria-label="Dismiss" onclick="hideToast()">×</button>';
  clearTimeout(window._toastTimer);
  if (type == "ok") window._toastTimer = setTimeout(hideToast, 4000);
}
function hideToast() {
  var t = document.getElementById("toast");
  if (t) t.className += " hide";
}

// Hộp thoại assign/reassign dùng chung cho Risk Queue và Order Detail
function openAssign(id, onDone) {
  var c = findCase(id);
  var list = specialists();
  var opts = '<option value="">-- Choose a specialist --</option>';
  for (var i = 0; i < list.length; i++) {
    var n = activeCount(list[i].id);
    opts += '<option value="' + list[i].id + '">' + list[i].name + " · " + n + "/" + config.capacity
      + (n >= config.capacity ? " (full)" : " · " + slotsLeft(list[i].id) + " slot(s) left") + "</option>";
  }
  var reassign = c.assignee != null;
  var body = '<p>Order <span class="id">' + shortId(id) + "</span> · " + badge(c.risk_level) + " " + c.risk_score.toFixed(2) + "</p>"
    + (reassign ? "<p>Current assignee: <b>" + userName(c.assignee) + "</b></p>" : "")
    + '<div class="form-row"><label for="as-user">' + (reassign ? "Move to" : "Assign to") + "</label><select id=\"as-user\">" + opts + "</select></div>"
    + '<div class="form-row"><label for="as-reason">Reason' + (reassign ? " (required)" : " (required if overriding)") + '</label>'
    + '<textarea id="as-reason" rows="2"></textarea></div>'
    + '<label class="check"><input type="checkbox" id="as-override"> Override capacity: allow assigning to someone who already holds ' + config.capacity + " orders</label>";
  openModal(reassign ? "Reassign order" : "Assign order", body, "Confirm", function () {
    var to = document.getElementById("as-user").value;
    var reason = document.getElementById("as-reason").value.trim();
    var override = document.getElementById("as-override").checked;
    if (!to) return { ok: false, msg: "Choose a specialist." };
    if ((reassign || override) && !reason) return { ok: false, msg: "Enter a reason: reassignments and overrides are recorded in the audit log." };
    var r = assignCase(id, to, reason, override);
    if (r.ok) { toast(r.msg); onDone(); }
    return r;
  });
}

// ---------- Giả lập trạng thái tải / lỗi (FRD F01-S02, F02-S05) ----------
// Chọn trong khung công cụ demo: normal | loading | error. Màn nào có dữ liệu tổng hợp thì đọc giá trị này.
function simState() {
  try { return localStorage.getItem("wf-sim") || "normal"; } catch (e) { return "normal"; }
}
function setSim(v) {
  try { localStorage.setItem("wf-sim", v); } catch (e) { }
  location.reload();
}
function skeletonHtml(rows) {
  var h = '<div class="skeleton" aria-busy="true" aria-label="Loading">';
  for (var i = 0; i < (rows || 4); i++) h += '<div class="sk-line" style="width:' + (92 - i * 9) + '%"></div>';
  return h + "</div>";
}
function errorHtml(what) {
  return '<div class="load-error" role="alert"><b>Couldn\'t load ' + what + ".</b> Check your connection and try again. "
    + '<button class="btn sm" type="button" onclick="setSim(\'normal\')">Retry</button></div>';
}

// ---------- Thanh điều hướng + chân trang ----------
// Specialist: Risk Queue. Manager: Dashboard, Risk Queue, Audit History. Order Detail chỉ hiện khi đang xem một đơn.
function renderChrome(active) {
  renderTopbar(active);
  if (document.querySelector(".wf-footer")) return;
  renderFooter();
}
function renderTopbar(active) {
  var u = me();
  // Mục theo vai (BRD 3.1, 3.2): mỗi mục là một màn thật. "My orders" là tab trong Risk Queue.
  var links = [];
  if (u.role == "manager") links.push(["overview.html", "Dashboard", "dashboard"]);
  links.push(["index.html", "Risk Queue", "queue"]);
  if (active == "detail") links.push([location.pathname.split("/").pop() + location.search, "Order Detail", "detail"]);
  if (u.role == "manager") links.push(["audit.html", "Audit History", "audit"]);

  var html = '<span class="logo"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 16 16"><rect x="2" y="9" width="3" height="5" rx="1" fill="currentColor"/>'
    + '<rect x="6.5" y="6" width="3" height="8" rx="1" fill="currentColor"/><rect x="11" y="2" width="3" height="12" rx="1" fill="currentColor"/></svg></span>Hidden Dissatisfaction</span>';
  for (var i = 0; i < links.length; i++) {
    html += '<a href="' + links[i][0] + '"' + (links[i][2] == active ? ' class="active" aria-current="page"' : "") + ">" + links[i][1] + "</a>";
  }
  var role = u.role == "manager" ? "Manager" : "Specialist";
  // Khu vực người dùng: avatar chữ viết tắt + tên/vai + nút Sign out (trên điện thoại chỉ còn avatar + nút)
  var parts = u.name.split(" "), initials = parts[0].charAt(0) + parts[parts.length - 1].charAt(0);
  html += '<span class="user"><span class="avatar" aria-hidden="true">' + initials + "</span>"
    + '<span class="u-text"><b>' + u.name + "</b><small>" + role + "</small></span>"
    + '<a class="signout" href="login.html" onclick="logout()" title="Sign out"><svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2.5H3.5v11H6M10 5l3 3-3 3M13 8H6"/></svg><span>Sign out</span></a></span>';
  document.getElementById("topbar").innerHTML = html;
}

function renderFooter() {
  var u = me();
  var opts = "";
  for (var j = 0; j < users.length; j++) {
    opts += '<option value="' + users[j].id + '"' + (users[j].id == u.id ? " selected" : "") + ">"
      + users[j].name + " – " + (users[j].role == "manager" ? "Manager" : "Specialist") + "</option>";
  }
  var sim = simState(), simOpts = "";
  var sims = [["normal", "Bình thường"], ["loading", "Đang tải"], ["error", "Lỗi tải dữ liệu"]];
  for (var k = 0; k < sims.length; k++) simOpts += '<option value="' + sims[k][0] + '"' + (sims[k][0] == sim ? " selected" : "") + ">" + sims[k][1] + "</option>";

  // Công cụ demo: KHÔNG thuộc sản phẩm. Bản thật vai lấy từ tài khoản đăng nhập, Backend kiểm tra quyền mỗi request.
  // Ẩn cùng nút "Ẩn/hiện ghi chú" để xem giao diện đúng như sản phẩm.
  var tools = document.createElement("div");
  tools.className = "wf-tools";
  tools.innerHTML = '<b>Công cụ demo prototype, không có trong sản phẩm.</b> '
    + "Bản thật: vai do tài khoản đăng nhập quyết định, người dùng không tự đổi được, Backend kiểm tra quyền độc lập.<br>"
    + '<label>Xem với vai: <select onchange="switchUser(this.value)">' + opts + "</select></label>"
    + ' · <label>Giả lập trạng thái: <select onchange="setSim(this.value)">' + simOpts + "</select></label>"
    + ' · <a href="#" onclick="resetData(); return false;">Đặt lại dữ liệu mẫu</a>'
    + " · Giờ giả lập: <b>" + viTime(NOW) + "</b>";
  document.body.appendChild(tools);

}
function switchUser(id) {
  try { localStorage.setItem("userId", id); } catch (e) { }
  location.reload();
}

// Màn chỉ dành cho Manager: Specialist mở thẳng địa chỉ thì báo không có quyền
function requireManager() {
  if (isManager()) return true;
  document.getElementById("content").innerHTML = '<div class="alert"><span class="icon">!</span>'
    + '<a class="btn" href="index.html">Back to Risk Queue</a>'
    + "<b>This page is for managers only.</b><br>Your specialist account doesn't have access.</div>"
    + '<div class="note">BRD 3.1: Specialist không có Dashboard riêng trong MVP.</div>';
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
  var on = false;
  try { on = localStorage.getItem("wf-present") == "1"; } catch (e) { }
  var q = new URLSearchParams(location.search).get("present");
  if (q != null) on = q == "1";
  setPresent(on);

  var box = document.createElement("div");
  box.className = "wf-btns";
  box.innerHTML = '<button type="button" class="wf-note-btn" onclick="toggleNotes()">Ghi chú: bật/tắt</button>'
    + '<button type="button" class="wf-note-btn" onclick="togglePresent()">Chế độ trình bày</button>';
  document.body.appendChild(box);

  document.addEventListener("keydown", function (e) {
    var t = e.target.tagName;
    if (e.key == "`" && t != "INPUT" && t != "TEXTAREA" && t != "SELECT") togglePresent();
  });
})();

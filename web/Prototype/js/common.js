// =========================================================
// common.js — hàm dùng chung cho mọi màn
// Gồm: nạp người dùng + cấu hình từ API, nhãn giao diện (tiếng Anh), định dạng, hộp thoại, thanh điều hướng.
// Dữ liệu lấy qua js/api.js. Luật nghiệp vụ (capacity, retry, SLA...) do backend kiểm tra và tính;
// frontend chỉ hiển thị và báo lỗi backend trả về (FRD mục 3).
// =========================================================

// ---------- Người đang đăng nhập + cấu hình (nạp một lần khi mở trang) ----------
var ME = null;        // GET /me
var config = null;    // GET /config (capacity, max_contact, sla_hours...)
var NOW = null;       // giờ của máy chủ, lấy từ GET /config

// Gọi đầu mỗi trang: nạp người dùng + cấu hình rồi vẽ thanh điều hướng.
// Chưa đăng nhập thì api.js tự chuyển về login.html.
async function boot(active) {
  try {
    var r = await Promise.all([api.getMe(), api.getConfig()]);
    ME = r[0]; config = r[1]; NOW = config.server_time;
  } catch (e) {
    if (e.status != 401) document.getElementById("content").innerHTML = errorHtml("your account");
    throw e;
  }
  renderChrome(active);
}
// Sau mỗi thao tác: nạp lại số đơn đang giữ và giờ máy chủ
async function reloadMe() {
  var r = await Promise.all([api.getMe(), api.getConfig()]);
  ME = r[0]; config = r[1]; NOW = config.server_time;
}

// Lỗi API → { ok: false, msg } để hộp thoại hiện ngay trong form
function apiFail(e) { return { ok: false, msg: e.message || "Something went wrong.", code: e.code }; }

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
var CONTACT_METHOD_LABEL = { PHONE: "Phone", EMAIL: "Email", MESSAGE: "Message" };

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
  return { code: c.sla_state, text: durationText(left) + (left < 0 ? " overdue" : " left") };
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
// Giá trị audit lưu mã (PENDING, HAS_ISSUE, NO_ANSWER…); hiển thị bằng nhãn giao diện cho dễ đọc
function humanValue(v) {
  if (!v) return v;
  var maps = [STATUS_LABEL, OUTCOME_LABEL, SKIP_LABEL, CONTACT_RESULT_LABEL];
  for (var m = 0; m < maps.length; m++) {
    for (var k in maps[m]) v = v.replace(new RegExp("\\b" + k + "\\b", "g"), maps[m][k]);
  }
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
  t.innerHTML = '<span class="toast-msg">' + msg + '</span><button type="button" class="toast-x" aria-label="Dismiss" onclick="hideToast()">×</button>';
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
  var opts = '<option value="">-- Choose a specialist --</option>';
  for (var i = 0; i < list.length; i++) {
    var n = list[i].active_count;
    opts += '<option value="' + list[i].user_id + '">' + list[i].full_name + " · " + n + "/" + config.capacity
      + (n >= config.capacity ? " (full)" : " · " + list[i].slots_left + " slot(s) left") + "</option>";
  }
  var reassign = c.assignee_id != null;
  var body = '<p>Order <span class="id">' + shortId(c.order_id) + "</span> · " + badge(c.risk_level) + " " + c.risk_score.toFixed(2) + "</p>"
    + (reassign ? "<p>Current assignee: <b>" + c.assignee_name + "</b></p>" : "")
    + '<div class="form-row"><label for="as-user">' + (reassign ? "Move to" : "Assign to") + "</label><select id=\"as-user\">" + opts + "</select></div>"
    + '<div class="form-row"><label for="as-reason">Reason' + (reassign ? " (required)" : " (required if overriding)") + '</label>'
    + '<textarea id="as-reason" rows="2"></textarea></div>'
    + '<label class="check"><input type="checkbox" id="as-override"> Override capacity: allow assigning to someone who already holds ' + config.capacity + " orders</label>";
  openModal(reassign ? "Reassign order" : "Assign order", body, "Confirm", async function () {
    var to = document.getElementById("as-user").value;
    var reason = document.getElementById("as-reason").value.trim();
    var override = document.getElementById("as-override").checked;
    // Kiểm tra nhanh trên form cho đỡ một lượt gọi; backend vẫn kiểm tra lại
    if (!to) return { ok: false, msg: "Choose a specialist." };
    if ((reassign || override) && !reason) return { ok: false, msg: "Enter a reason: reassignments and overrides are recorded in the audit log." };
    try {
      var r = await api.assign(c.order_id, to, reason, override);
      toast(r.previous_assignee_name
        ? "Moved order " + shortId(c.order_id) + " from " + r.previous_assignee_name + " to " + r.order.assignee_name + "."
        : "Assigned order " + shortId(c.order_id) + " to " + r.order.assignee_name + ".");
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
  var h = '<div class="skeleton" aria-busy="true" aria-label="Loading">';
  for (var i = 0; i < (rows || 4); i++) h += '<div class="sk-line" style="width:' + (92 - i * 9) + '%"></div>';
  return h + "</div>";
}
function errorHtml(what) {
  return '<div class="load-error" role="alert"><b>Couldn\'t load ' + what + ".</b> Check your connection and try again. "
    + '<button class="btn sm" type="button" onclick="location.reload()">Retry</button></div>';
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
  if (u.role == "MANAGER") links.push(["overview.html", "Dashboard", "dashboard"]);
  links.push(["index.html", "Risk Queue", "queue"]);
  if (active == "detail") links.push([location.pathname.split("/").pop() + location.search, "Order Detail", "detail"]);
  if (u.role == "MANAGER") links.push(["audit.html", "Audit History", "audit"]);

  var html = '<span class="logo"><span class="brand-mark" aria-hidden="true"><svg viewBox="0 0 16 16"><rect x="2" y="9" width="3" height="5" rx="1" fill="currentColor"/>'
    + '<rect x="6.5" y="6" width="3" height="8" rx="1" fill="currentColor"/><rect x="11" y="2" width="3" height="12" rx="1" fill="currentColor"/></svg></span>Hidden Dissatisfaction</span>';
  for (var i = 0; i < links.length; i++) {
    html += '<a href="' + links[i][0] + '"' + (links[i][2] == active ? ' class="active" aria-current="page"' : "") + ">" + links[i][1] + "</a>";
  }
  var role = u.role == "MANAGER" ? "Manager" : "Specialist";
  // Khu vực người dùng: avatar chữ viết tắt + tên/vai + nút Sign out (trên điện thoại chỉ còn avatar + nút)
  var parts = u.full_name.split(" "), initials = parts[0].charAt(0) + parts[parts.length - 1].charAt(0);
  html += '<span class="user"><span class="avatar" aria-hidden="true">' + initials + "</span>"
    + '<span class="u-text"><b>' + u.full_name + "</b><small>" + role + "</small></span>"
    + '<a class="signout" href="login.html" onclick="logout(); return false;" title="Sign out"><svg viewBox="0 0 16 16" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2.5H3.5v11H6M10 5l3 3-3 3M13 8H6"/></svg><span>Sign out</span></a></span>';
  document.getElementById("topbar").innerHTML = html;
}

function renderFooter() {
  // Công cụ demo: KHÔNG thuộc sản phẩm, chỉ có khi đang dùng backend giả.
  // Ẩn cùng nút "Ẩn/hiện ghi chú" để xem giao diện đúng như sản phẩm.
  if (!API_CONFIG.USE_MOCK) return;
  var u = me(), accounts = [["u2", "nhanvien", "Trần Thị B – Specialist"], ["u3", "nhanvien2", "Lê Văn C – Specialist"], ["u4", "quanly", "Phạm Văn D – Manager"]];
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
  tools.innerHTML = '<b>Công cụ demo prototype, không có trong sản phẩm.</b> '
    + "Đang dùng backend giả (js/mock-server.js) theo API_CONTRACT_olist_hidden_dissatisfaction.md. Bản thật: vai do tài khoản quyết định, Backend kiểm tra quyền.<br>"
    + '<label>Đăng nhập lại với: <select onchange="switchUser(this.value)">' + opts + "</select></label>"
    + ' · <label>Giả lập mạng: <select onchange="setSim(this.value)">' + simOpts + "</select></label>"
    + ' · <a href="#" onclick="resetData(); return false;">Đặt lại dữ liệu mẫu</a>'
    + " · Giờ máy chủ giả: <b>" + viTime(NOW) + "</b>";
  document.body.appendChild(tools);
}
async function switchUser(username) {
  await api.login(username, "123456");
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

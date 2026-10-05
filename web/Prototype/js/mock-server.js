// =========================================================
// mock-server.js — BACKEND GIẢ chạy ngay trong trình duyệt
// Trả lời đúng các endpoint trong API_CONTRACT_olist_hidden_dissatisfaction.md (đường dẫn, JSON, mã lỗi HTTP),
// để frontend làm trước khi backend thật xong. Frontend chỉ gọi qua js/api.js, không gọi file này trực tiếp.
// Luật nghiệp vụ (BRD mục 6) nằm ở đây, đúng chỗ của nó ở bản thật: backend kiểm tra, frontend chỉ hiển thị.
// Khi có backend thật: bỏ mock-data.js + mock-server.js khỏi các trang, api.js tự chuyển sang gọi fetch.
// =========================================================

var MockServer = (function () {
  var STORE_KEY = "hd-mock-db-v2";   // đổi khi đổi tên field, để trình duyệt bỏ dữ liệu lưu theo tên cũ
  var db;

  // ---------- Lưu tạm vào trình duyệt để chuyển màn không mất ----------
  function load() {
    var base = JSON.parse(JSON.stringify(MOCK_DB));
    try {
      var saved = localStorage.getItem(STORE_KEY);
      if (saved != null) {
        var d = JSON.parse(saved);
        base.cases = d.cases; base.contacts = d.contacts; base.audits = d.audits; base.now = d.now;
      }
    } catch (e) { /* không đọc được thì dùng dữ liệu mẫu */ }
    for (var i = 0; i < base.cases.length; i++) {
      var c = base.cases[i];
      if (c.model_version == null) c.model_version = "hd-model v0.3 (LightGBM)";
      if (c.predicted_at == null) c.predicted_at = c.queued_at;
      if (c.reopen_count == null) c.reopen_count = 0;
    }
    return base;
  }
  function save() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ cases: db.cases, contacts: db.contacts, audits: db.audits, now: db.now }));
    } catch (e) { }
  }
  function reset() {
    try { localStorage.removeItem(STORE_KEY); } catch (e) { }
    db = load();
  }
  db = load();
  var cfg = db.config;

  // ---------- Thời gian (bản thật dùng business calendar có ngày lễ) ----------
  function parseTime(s) {
    var p = s.split(/[- :T]/);
    return new Date(+p[0], +p[1] - 1, +p[2], +(p[3] || 0), +(p[4] || 0));
  }
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  function fmtTime(d) {
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
  }
  function hoursBetween(a, b) { return (parseTime(b) - parseTime(a)) / 3600000; }
  // Mỗi thao tác đẩy đồng hồ giả lên 1 phút để lịch sử có thứ tự
  function tick() {
    var d = parseTime(db.now);
    d.setMinutes(d.getMinutes() + 1);
    db.now = fmtTime(d);
    return db.now;
  }

  // ---------- Tra cứu ----------
  function findCase(id) {
    for (var i = 0; i < db.cases.length; i++) if (db.cases[i].order_id == id) return db.cases[i];
    return null;
  }
  function findUser(id) {
    for (var i = 0; i < db.users.length; i++) if (db.users[i].id == id) return db.users[i];
    return null;
  }
  function userName(id) { var u = findUser(id); return u ? u.full_name : null; }
  function isClosed(c) { return c.status == "COMPLETED" || c.status == "SKIPPED"; }
  function contactsOf(id) {
    var list = [];
    for (var i = 0; i < db.contacts.length; i++) if (db.contacts[i].order_id == id) list.push(db.contacts[i]);
    list.sort(function (a, b) { return parseTime(a.at) - parseTime(b.at); });
    return list;
  }
  function auditsOf(id) {
    var list = [];
    for (var i = 0; i < db.audits.length; i++) if (id == null || db.audits[i].order_id == id) list.push(db.audits[i]);
    list.sort(function (a, b) { return parseTime(b.at) - parseTime(a.at); });   // mới nhất lên đầu
    return list;
  }

  // ---------- Capacity (BRD 6.3) ----------
  function activeCount(userId) {
    var n = 0;
    for (var i = 0; i < db.cases.length; i++) if (db.cases[i].assignee == userId && db.cases[i].status == "IN_PROGRESS") n++;
    return n;
  }

  // ---------- SLA, aging, escalation (BRD 6.7) ----------
  function slaDue(c) {
    var d = parseTime(c.queued_at);
    d.setHours(d.getHours() + cfg.sla_hours[c.risk_level]);
    return fmtTime(d);
  }
  function slaState(c) {
    if (isClosed(c)) return "none";
    var left = hoursBetween(db.now, slaDue(c));
    if (left < 0) return "over";
    if (left < cfg.soon_hours) return "soon";
    return "ok";
  }
  function agingHours(c) { return hoursBetween(c.queued_at, isClosed(c) ? c.updated_at : db.now); }
  function isEscalated(c) { return !isClosed(c) && agingHours(c) >= cfg.aging_days * 24; }
  function isStale(c) { return c.status == "IN_PROGRESS" && hoursBetween(c.updated_at, db.now) >= cfg.stale_hours; }

  // score giảm dần → gần quá SLA hơn → nằm queue lâu hơn (BRD 6.2)
  function byPriority(a, b) {
    if (b.risk_score != a.risk_score) return b.risk_score - a.risk_score;
    var sa = parseTime(slaDue(a)), sb = parseTime(slaDue(b));
    if (sa - sb != 0) return sa - sb;
    return parseTime(a.queued_at) - parseTime(b.queued_at);
  }

  // ---------- Định dạng trả về (API_CONTRACT mục 3) ----------
  function orderOut(c) {
    var o = {};
    for (var k in c) if (k.charAt(0) != "_" && k != "assignee") o[k] = c[k];
    o.case_id = "case-" + c.order_id.substring(0, 8);   // bản thật: app.review_cases.case_id (uuid)
    o.assignee_id = c.assignee || null;
    o.assignee_name = userName(c.assignee);
    o.closed_at = isClosed(c) ? c.updated_at : null;
    o.threshold_version = cfg.threshold_version;
    o.suggested_action = { HIGH: "CONTACT", MEDIUM: "MONITOR", LOW: "NO_ACTION" }[c.risk_level];
    o.outcome = c.outcome || null;
    o.skip_reason = c.skip_reason || null;
    o.sla_due_at = isClosed(c) ? null : slaDue(c);
    o.sla_state = slaState(c);
    o.sla_hours_left = isClosed(c) ? null : Math.round(hoursBetween(db.now, slaDue(c)) * 100) / 100;
    o.aging_hours = Math.round(agingHours(c) * 100) / 100;
    o.is_escalated = isEscalated(c);
    o.is_stale = isStale(c);
    o.stale_hours = c.status == "IN_PROGRESS" ? Math.round(hoursBetween(c.updated_at, db.now) * 100) / 100 : null;
    o.contact_count = contactsOf(c.order_id).length;
    return o;
  }
  function contactOut(x, i) {
    return { contact_id: x.order_id.substring(0, 8) + "-" + (i + 1), attempt_no: i + 1, contacted_at: x.at,
      method: x.method, result: x.result, note: x.note || "", next_contact_date: x.next_date || null,
      created_by: x.user, created_by_name: userName(x.user) };
  }
  var OVERRIDE_TYPES = ["REASSIGN", "REOPEN", "OVERRIDE"];
  function auditOut(e) {
    var c = findCase(e.order_id), all = auditsOf(e.order_id), over = false;
    for (var i = 0; i < all.length; i++) if (OVERRIDE_TYPES.indexOf(all[i].type) != -1) over = true;
    return { created_at: e.at, actor_id: e.actor, actor_name: userName(e.actor), order_id: e.order_id, event_type: e.type,
      old_value: e.old_value, new_value: e.new_value, reason: e.reason || "",
      order: c ? { status: c.status, risk_level: c.risk_level, assignee_name: userName(c.assignee), event_count: all.length, has_override: over } : null };
  }
  function meOut(u) {
    var n = activeCount(u.id);
    var sp = u.role == "SPECIALIST";
    return { user_id: u.id, full_name: u.full_name, role: u.role, active_count: sp ? n : null,
      capacity: cfg.capacity, slots_left: sp ? Math.max(0, cfg.capacity - n) : null };
  }

  // ---------- Phản hồi ----------
  function ok(body, status) { return { status: status || 200, body: body }; }
  function fail(status, code, message, details) {
    return { status: status, body: { error: { code: code, message: message, details: details || null } } };
  }
  function addAudit(actor, orderId, type, oldValue, newValue, reason) {
    db.audits.push({ at: tick(), actor: actor, order_id: orderId, type: type, old_value: oldValue, new_value: newValue, reason: reason || "" });
  }
  function shortId(id) { return id.substring(0, 8) + "…"; }

  // ---------- GET /orders: lọc + sắp xếp + phân trang (FRD F02, F03) ----------
  function match(c, q, me) {
    if (q.q && c.order_id.indexOf(q.q) != 0) return false;
    if (q.level && c.risk_level != q.level) return false;
    if (q.smin != null && q.smin !== "" && c.risk_score < +q.smin) return false;
    if (q.smax != null && q.smax !== "" && c.risk_score > +q.smax) return false;
    if (q.status == "OPEN" && isClosed(c)) return false;
    if (q.status && q.status != "OPEN" && c.status != q.status) return false;
    if (q.outcome) {
      var kind = q.outcome.substring(0, 1), code = q.outcome.substring(2);
      if (kind == "O" && !(c.status == "COMPLETED" && c.outcome == code)) return false;
      if (kind == "S" && !(c.status == "SKIPPED" && c.skip_reason == code)) return false;
    }
    if (q.seller && c.seller_id != q.seller) return false;
    if (q.category && c.category != q.category) return false;
    if (q.from && c.queued_at.substring(0, 10) < q.from) return false;
    if (q.to && c.queued_at.substring(0, 10) > q.to) return false;
    if (q.assignee == "me" && c.assignee != me.id) return false;
    if (q.assignee == "none" && c.assignee != null) return false;
    if (q.assignee && q.assignee != "me" && q.assignee != "none" && c.assignee != q.assignee) return false;
    if (q.sla == "over" && slaState(c) != "over") return false;
    if (q.sla == "soon" && slaState(c) != "soon") return false;
    if (q.sla == "esc" && !isEscalated(c)) return false;
    if (q.sla == "stale" && !isStale(c)) return false;
    return true;
  }
  function listOrders(q, me) {
    if (q.q && !/^[0-9a-f]{1,32}$/.test(q.q)) return fail(400, "INVALID_ORDER_ID", "An order ID only contains 0-9 and a-f, at most 32 characters.");
    var list = [];
    for (var i = 0; i < db.cases.length; i++) if (match(db.cases[i], q, me)) list.push(db.cases[i]);
    list.sort(function (a, b) {
      if (q.sort == "sla") {
        var d = (isClosed(a) ? 1 : 0) - (isClosed(b) ? 1 : 0);   // đơn đã đóng không có SLA, để cuối
        return d != 0 ? d : (parseTime(slaDue(a)) - parseTime(slaDue(b))) || byPriority(a, b);
      }
      if (q.sort == "aging") return (agingHours(b) - agingHours(a)) || byPriority(a, b);
      return byPriority(a, b);
    });
    var limit = Math.min(+q.limit || 20, 100), offset = +q.offset || 0, items = [];
    for (var j = offset; j < list.length && j < offset + limit; j++) items.push(orderOut(list[j]));
    return ok({ items: items, total: list.length, limit: limit, offset: offset });
  }

  // GET /orders/summary: banner Risk Queue (F02-S01)
  function summary(me) {
    var s = { high_pending: 0, high_pending_overdue: 0, overdue: 0, escalated: 0, stale: 0, first_pending: null };
    var list = db.cases.slice().sort(byPriority);
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      if (c.status == "PENDING" && s.first_pending == null) s.first_pending = orderOut(c);
      if (c.status == "PENDING" && c.risk_level == "HIGH") { s.high_pending++; if (slaState(c) == "over") s.high_pending_overdue++; }
      if (slaState(c) == "over") s.overdue++;
      if (isEscalated(c)) s.escalated++;
      if (isStale(c)) s.stale++;
    }
    s.me = meOut(me);
    return ok(s);
  }

  function filterOptions() {
    var sellers = [], cats = [];
    for (var i = 0; i < db.cases.length; i++) {
      if (sellers.indexOf(db.cases[i].seller_id) == -1) sellers.push(db.cases[i].seller_id);
      if (cats.indexOf(db.cases[i].category) == -1) cats.push(db.cases[i].category);
    }
    cats.sort();
    return ok({ sellers: sellers, categories: cats });
  }

  // GET /orders/{id}: chi tiết + liên lạc + ghi chú model + audit (chỉ Manager) (F04)
  function orderDetail(id, me) {
    var c = findCase(id);
    if (!c) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    var notes = [], audits = auditsOf(id), same = 0;
    for (var i = 0; i < audits.length; i++) {
      if (audits[i].type == "MODEL_NOTE") notes.push({ created_at: audits[i].at, actor_id: audits[i].actor, actor_name: userName(audits[i].actor), note: audits[i].reason });
    }
    for (var j = 0; j < db.cases.length; j++) if (db.cases[j].seller_id == c.seller_id && !isClosed(db.cases[j]) && db.cases[j] != c) same++;
    return ok({
      order: orderOut(c),
      contacts: contactsOf(id).map(contactOut),
      model_notes: notes,
      audit_events: me.role == "MANAGER" ? audits.map(auditOut) : null,
      seller_open_count: same
    });
  }

  // ---------- Thao tác (F05–F08) ----------
  function needManager(me) { return me.role == "MANAGER" ? null : fail(403, "FORBIDDEN", "Only managers can do this."); }

  function claim(id, me) {
    var c = findCase(id);
    if (!c) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    if (me.role != "SPECIALIST") return fail(403, "FORBIDDEN", "Managers assign orders instead of claiming them.");
    if (c._conflict) {   // giả lập: người khác bấm trước một nhịp (F05-S03)
      c._conflict = false;
      c.status = "IN_PROGRESS"; c.assignee = "u1"; c.updated_at = db.now;
      db.audits.push({ at: db.now, actor: "u1", order_id: id, type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · " + userName("u1"), reason: "" });
      save();
      return fail(409, "ALREADY_CLAIMED", "Order " + shortId(id) + " was just claimed by " + userName("u1") + ".", { assignee_name: userName("u1") });
    }
    if (c.status != "PENDING") return fail(409, "INVALID_STATE", "This order is no longer pending.");
    if (activeCount(me.id) >= cfg.capacity) {
      return fail(422, "CAPACITY_FULL", "You already hold " + cfg.capacity + " orders. Complete or skip one to claim more.");
    }
    c.status = "IN_PROGRESS"; c.assignee = me.id; c.updated_at = tick();
    addAudit(me.id, id, "CLAIM", "PENDING · (none)", "IN_PROGRESS · " + me.full_name);
    save();
    return ok({ order: orderOut(c), me: meOut(me) });
  }

  function assign(id, body, me) {
    var deny = needManager(me); if (deny) return deny;
    var c = findCase(id);
    if (!c) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    var to = findUser(body.assignee_id), reason = (body.reason || "").trim(), override = !!body.override_capacity;
    if (!to || to.role != "SPECIALIST") return fail(422, "VALIDATION_ERROR", "Choose a specialist.", { field: "assignee_id" });
    if (isClosed(c)) return fail(409, "INVALID_STATE", "Closed orders must be reopened before assigning.");
    var from = c.assignee;
    if (from == to.id) return fail(422, "VALIDATION_ERROR", "That specialist is already the assignee.", { field: "assignee_id" });
    if ((from != null || override) && !reason) return fail(422, "REASON_REQUIRED", "Enter a reason: reassignments and overrides are recorded in the audit log.", { field: "reason" });
    var n = activeCount(to.id);
    if (n >= cfg.capacity) {
      if (!override) return fail(422, "CAPACITY_FULL", to.full_name + " already holds " + cfg.capacity + " orders. Tick \"Override capacity\" and enter a reason.");
      addAudit(me.id, id, "OVERRIDE", to.full_name + ": " + n + "/" + cfg.capacity + " active", (n + 1) + "/" + cfg.capacity + " (over capacity)", reason);
    }
    if (from == null) {
      c.status = "IN_PROGRESS"; c.assignee = to.id; c.updated_at = tick();
      addAudit(me.id, id, "ASSIGN", "PENDING · (none)", "IN_PROGRESS · " + to.full_name, reason);
    } else {
      c.assignee = to.id; c.updated_at = tick();
      addAudit(me.id, id, "REASSIGN", userName(from), to.full_name, reason);
    }
    save();
    return ok({ order: orderOut(c), previous_assignee_name: userName(from) });
  }

  function addContact(id, body, me) {
    var c = findCase(id);
    if (!c) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    if (c.status != "IN_PROGRESS") return fail(409, "INVALID_STATE", "Only in-progress orders can log contact attempts.");
    if (c.assignee != me.id) return fail(403, "FORBIDDEN", "Only the assignee can log contact attempts.");
    var n = contactsOf(id).length;
    if (n >= cfg.max_contact) return fail(422, "MAX_CONTACTS_REACHED", "All " + cfg.max_contact + " contact attempts are used; attempt " + (n + 1) + " is not allowed.");
    var at = (body.contacted_at || "").replace("T", " ");
    if (!at || !body.method || !body.result) return fail(422, "VALIDATION_ERROR", "Time, method and result are required.");
    if (at > db.now) return fail(422, "VALIDATION_ERROR", "Contact time cannot be in the future.", { field: "contacted_at" });
    tick();
    var x = { order_id: id, at: at, user: me.id, method: body.method, result: body.result, note: body.note || "", next_date: body.next_contact_date || "" };
    db.contacts.push(x);
    c.updated_at = db.now;
    addAudit(me.id, id, "CONTACT", n + "/" + cfg.max_contact, (n + 1) + "/" + cfg.max_contact + " · " + body.result, "");
    save();
    return ok({ contact: contactOut(x, n), order: orderOut(c) }, 201);
  }

  function canWork(c, me) { return c.assignee == me.id || me.role == "MANAGER"; }

  function complete(id, body, me) {
    var c = findCase(id);
    if (!c) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    if (c.status != "IN_PROGRESS") return fail(409, "INVALID_STATE", "Only in-progress orders can be completed.");
    if (!canWork(c, me)) return fail(403, "FORBIDDEN", "Only the assignee or a manager can complete this order.");
    var outcome = body.outcome;
    if (["HAS_ISSUE", "NO_ISSUE", "UNREACHABLE", "DUPLICATE"].indexOf(outcome) == -1) return fail(422, "VALIDATION_ERROR", "Choose an outcome before completing.", { field: "outcome" });
    if (outcome == "UNREACHABLE" && contactsOf(id).length < cfg.max_contact) {
      return fail(422, "OUTCOME_NOT_ALLOWED", "\"Unreachable\" needs " + cfg.max_contact + " contact attempts first.", { field: "outcome" });
    }
    c.status = "COMPLETED"; c.outcome = outcome; c.updated_at = tick();
    addAudit(me.id, id, "STATUS", "IN_PROGRESS", "COMPLETED · " + outcome, body.note || "");
    save();
    return ok({ order: orderOut(c) });
  }

  function skip(id, body, me) {
    var c = findCase(id);
    if (!c) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    if (c.status != "IN_PROGRESS") return fail(409, "INVALID_STATE", "Only in-progress orders can be skipped.");
    if (!canWork(c, me)) return fail(403, "FORBIDDEN", "Only the assignee or a manager can skip this order.");
    var reason = body.reason, note = (body.note || "").trim();
    if (["UNREACHABLE", "DUPLICATE", "REFUSED", "NOT_APPLICABLE", "OTHER"].indexOf(reason) == -1) return fail(422, "VALIDATION_ERROR", "Choose a skip reason.", { field: "reason" });
    if (reason == "OTHER" && !note) return fail(422, "VALIDATION_ERROR", "\"Other\" requires a note.", { field: "note" });
    c.status = "SKIPPED"; c.skip_reason = reason; c.updated_at = tick();
    addAudit(me.id, id, "SKIP", "IN_PROGRESS", "SKIPPED", reason + (note ? ": " + note : ""));
    save();
    return ok({ order: orderOut(c) });
  }

  function reopen(id, body, me) {
    var deny = needManager(me); if (deny) return deny;
    var c = findCase(id);
    if (!c) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    if (!isClosed(c)) return fail(409, "INVALID_STATE", "Only completed or skipped orders can be reopened.");
    var reason = (body.reason || "").trim();
    if (!reason) return fail(422, "REASON_REQUIRED", "A reason is required to reopen.", { field: "reason" });
    var closedDays = hoursBetween(c.updated_at, db.now) / 24;
    if ((closedDays > cfg.reopen_review_days || c.reopen_count >= cfg.reopen_review_times) && !body.review_confirmed) {
      return fail(422, "REVIEW_CONFIRMATION_REQUIRED", "Tick the review confirmation before reopening.");
    }
    var old = c.status + (c.outcome ? " · " + c.outcome : (c.skip_reason ? " · " + c.skip_reason : ""));
    c.status = "PENDING"; c.assignee = null; c.outcome = null; c.skip_reason = null;
    c.reopen_count++; c.queued_at = tick(); c.updated_at = db.now;
    addAudit(me.id, id, "REOPEN", old, "PENDING", reason);
    save();
    return ok({ order: orderOut(c) });
  }

  function modelNote(id, body, me) {
    var deny = needManager(me); if (deny) return deny;
    if (!findCase(id)) return fail(404, "ORDER_NOT_FOUND", "Order " + id + " was not found.");
    var note = (body.note || "").trim();
    if (!note) return fail(422, "VALIDATION_ERROR", "Enter a note.", { field: "note" });
    addAudit(me.id, id, "MODEL_NOTE", "", "Flagged for model review", note);
    save();
    return ok({ created_at: db.now, actor_id: me.id, actor_name: me.full_name, note: note }, 201);
  }

  // ---------- GET /dashboard (F01): mọi số liệu tổng hợp tính ở backend ----------
  function dashboard(q, me) {
    var deny = needManager(me); if (deny) return deny;
    var from = "";
    if (q.days) { var d = parseTime(db.now.substring(0, 10)); d.setDate(d.getDate() - (+q.days - 1)); from = fmtTime(d).substring(0, 10); }
    var data = [];
    for (var i = 0; i < db.cases.length; i++) {
      var c = db.cases[i];
      if (from && c.queued_at.substring(0, 10) < from) continue;
      if (q.level && c.risk_level != q.level) continue;
      if (q.seller && c.seller_id != q.seller) continue;
      if (q.category && c.category != q.category) continue;
      if (q.assignee && c.assignee != q.assignee) continue;
      if (q.status && c.status != q.status) continue;
      data.push(c);
    }
    var t = { total: data.length, PENDING: 0, IN_PROGRESS: 0, COMPLETED: 0, SKIPPED: 0, high_pending: 0, high_pending_overdue: 0, overdue: 0, stale: 0 };
    var r = { closed: 0, completed: 0, skipped: 0, unreachable: 0, issue_found: 0 };
    var lv = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    var bands = [[0.8, 1.0], [0.6, 0.8], [0.4, 0.6], [0.2, 0.4], [0, 0.2]], bandOut = [];
    for (var b = 0; b < bands.length; b++) bandOut.push({ min: bands[b][0], max: bands[b][1], count: 0, open: 0 });
    var groups = { seller: {}, category: {} };
    for (var j = 0; j < data.length; j++) {
      var x = data[j];
      t[x.status]++;
      lv[x.risk_level]++;
      if (x.risk_level == "HIGH" && x.status == "PENDING") { t.high_pending++; if (slaState(x) == "over") t.high_pending_overdue++; }
      if (slaState(x) == "over") t.overdue++;
      if (isStale(x)) t.stale++;
      if (isClosed(x)) {
        r.closed++;
        if (x.status == "COMPLETED") { r.completed++; if (x.outcome == "HAS_ISSUE") r.issue_found++; if (x.outcome == "UNREACHABLE") r.unreachable++; }
        if (x.status == "SKIPPED") { r.skipped++; if (x.skip_reason == "UNREACHABLE") r.unreachable++; }
      }
      for (var k = 0; k < bandOut.length; k++) {
        var lo = bandOut[k].min, hi = bandOut[k].max;
        if (x.risk_score >= lo && (x.risk_score < hi || (hi == 1 && x.risk_score <= 1))) { bandOut[k].count++; if (!isClosed(x)) bandOut[k].open++; break; }
      }
      var keys = { seller: x.seller_id, category: x.category };
      for (var g in keys) {
        var m = groups[g][keys[g]];
        if (!m) m = groups[g][keys[g]] = { key: keys[g], total: 0, high: 0, open: 0, related: [] };
        m.total++;
        if (x.risk_level == "HIGH") m.high++;
        if (!isClosed(x)) m.open++;
        var rel = g == "seller" ? x.category : x.seller_id;
        if (m.related.indexOf(rel) == -1) m.related.push(rel);
      }
    }
    function sortGroup(obj) {
      var list = [];
      for (var key in obj) list.push(obj[key]);
      return list.sort(function (a, b) { return (b.high - a.high) || (b.open - a.open) || (b.total - a.total); });
    }
    var workload = [];
    for (var u = 0; u < db.users.length; u++) {
      var usr = db.users[u];
      if (usr.role != "SPECIALIST" || (q.assignee && q.assignee != usr.id)) continue;
      var w = { user_id: usr.id, full_name: usr.full_name, active_count: activeCount(usr.id), capacity: cfg.capacity,
        slots_left: Math.max(0, cfg.capacity - activeCount(usr.id)), overdue: 0, stale: 0, completed: 0, has_data: false };
      for (var y = 0; y < data.length; y++) {
        if (data[y].assignee != usr.id) continue;
        w.has_data = true;
        if (data[y].status == "IN_PROGRESS" && slaState(data[y]) == "over") w.overdue++;
        if (isStale(data[y])) w.stale++;
        if (data[y].status == "COMPLETED") w.completed++;
      }
      workload.push(w);
    }
    var attention = [], sortedData = data.slice().sort(byPriority);
    for (var a = 0; a < sortedData.length; a++) {
      var z = sortedData[a], why = [];
      if (slaState(z) == "over" && z.risk_level == "HIGH") why.push({ code: "SLA_OVERDUE" });
      if (isEscalated(z)) why.push({ code: "ESCALATED", hours: Math.round(agingHours(z) * 100) / 100 });
      if (isStale(z)) why.push({ code: "STALE", hours: Math.round(hoursBetween(z.updated_at, db.now) * 100) / 100, assignee_name: userName(z.assignee) });
      if (why.length) attention.push({ order: orderOut(z), reasons: why });
    }
    var recent = [], ev = auditsOf(null);
    for (var e = 0; e < ev.length && recent.length < 5; e++) {
      if (["ASSIGN", "REASSIGN", "REOPEN", "OVERRIDE"].indexOf(ev[e].type) != -1) recent.push(auditOut(ev[e]));
    }
    return ok({
      as_of: db.now, from: from || null, totals: t, rates: r,
      by_level: [{ level: "HIGH", count: lv.HIGH }, { level: "MEDIUM", count: lv.MEDIUM }, { level: "LOW", count: lv.LOW }],
      score_bands: bandOut, by_seller: sortGroup(groups.seller), by_category: sortGroup(groups.category),
      workload: workload, attention: attention, recent_overrides: recent
    });
  }

  function auditEvents(q, me) {
    var deny = needManager(me); if (deny) return deny;
    var ev = auditsOf(null), items = [];
    for (var i = 0; i < ev.length; i++) {
      var e = ev[i];
      if (q.event_type && e.type != q.event_type) continue;
      if (q.actor_id && e.actor != q.actor_id) continue;
      if (q.order_id && e.order_id.indexOf(q.order_id) != 0) continue;
      if (q.override_only == "true" && OVERRIDE_TYPES.indexOf(e.type) == -1) continue;
      items.push(auditOut(e));
    }
    return ok({ items: items, total: items.length, all_total: db.audits.length });
  }

  // ---------- Bộ định tuyến ----------
  function userFromToken(token) {
    if (!token || token.indexOf("mock-token-") != 0) return null;
    return findUser(token.substring("mock-token-".length));
  }

  function route(method, path, query, body, token) {
    db = load(); cfg = db.config;   // trang khác có thể vừa ghi dữ liệu
    if (method == "POST" && path == "/auth/login") {
      for (var i = 0; i < db.accounts.length; i++) {
        var a = db.accounts[i];
        if (a.username == body.username && a.password == body.password) {
          return ok({ token: "mock-token-" + a.user_id, user: meOut(findUser(a.user_id)) });
        }
      }
      return fail(401, "INVALID_CREDENTIALS", "Incorrect username or password.");
    }
    var me = userFromToken(token);
    if (!me) return fail(401, "UNAUTHENTICATED", "Please sign in.");
    if (method == "POST" && path == "/auth/logout") return { status: 204, body: null };
    if (method == "GET" && path == "/me") return ok(meOut(me));
    if (method == "GET" && path == "/config") {
      var out = {};
      for (var k in cfg) out[k] = cfg[k];
      out.server_time = db.now;
      return ok(out);
    }
    if (method == "GET" && path == "/users") {
      var list = [];
      for (var u = 0; u < db.users.length; u++) if (!query.role || db.users[u].role == query.role) list.push(meOut(db.users[u]));
      return ok({ items: list });
    }
    if (method == "GET" && path == "/orders") return listOrders(query, me);
    if (method == "GET" && path == "/orders/summary") return summary(me);
    if (method == "GET" && path == "/orders/filter-options") return filterOptions();
    if (method == "GET" && path == "/dashboard") return dashboard(query, me);
    if (method == "GET" && path == "/audit-events") return auditEvents(query, me);
    var m = path.match(/^\/orders\/([0-9a-f]{32})(\/[a-z-]+)?$/);
    if (m) {
      var id = m[1], action = m[2] || "";
      if (method == "GET" && action == "") return orderDetail(id, me);
      if (method == "POST" && action == "/claim") return claim(id, me);
      if (method == "POST" && action == "/assign") return assign(id, body, me);
      if (method == "POST" && action == "/contacts") return addContact(id, body, me);
      if (method == "POST" && action == "/complete") return complete(id, body, me);
      if (method == "POST" && action == "/skip") return skip(id, body, me);
      if (method == "POST" && action == "/reopen") return reopen(id, body, me);
      if (method == "POST" && action == "/model-notes") return modelNote(id, body, me);
    }
    return fail(404, "NOT_FOUND", "No endpoint " + method + " " + path);
  }

  // Giả lập mạng: chậm hoặc lỗi theo ô "Giả lập trạng thái" trong khung công cụ demo
  function sim() { try { return localStorage.getItem("wf-sim") || "normal"; } catch (e) { return "normal"; } }

  function handle(method, path, query, body, token) {
    var mode = sim();
    var delay = mode == "loading" ? 2500 : 120;
    return new Promise(function (resolve) {
      setTimeout(function () {
        if (mode == "error" && method == "GET" && path != "/me" && path != "/config") {
          resolve(fail(500, "SERVER_ERROR", "Simulated server error."));
          return;
        }
        resolve(route(method, path, query || {}, body || {}, token));
      }, delay);
    });
  }

  return { handle: handle, reset: reset };
})();

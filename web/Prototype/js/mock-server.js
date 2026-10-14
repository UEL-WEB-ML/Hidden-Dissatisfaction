// =========================================================
// mock-server.js — BACKEND GIẢ chạy ngay trong trình duyệt
// Trả lời đúng các endpoint trong API_CONTRACT_olist_hidden_dissatisfaction.md v0.2 (đường dẫn, JSON, mã lỗi HTTP),
// để frontend làm trước khi backend thật xong. Frontend chỉ gọi qua js/api.js, không gọi file này trực tiếp.
// Luật nghiệp vụ (BRD v4.0 mục 6) nằm ở đây, đúng chỗ của nó ở bản thật: backend kiểm tra, frontend chỉ hiển thị.
// Khi có backend thật: bỏ mock-data.js + mock-server.js khỏi các trang, api.js tự chuyển sang gọi fetch.
// =========================================================

var MockServer = (function () {
  var STORE_KEY = "hd-mock-db-v3";   // đổi khi đổi cấu trúc dữ liệu, để trình duyệt bỏ dữ liệu lưu theo cấu trúc cũ
  var SAVED = ["cases", "contacts", "audits", "now", "comments", "decisions", "params", "users"];
  var db;
  var LANG = "en";   // ngôn ngữ của câu thông báo lỗi, lấy từ header Accept-Language của từng request

  // Câu thông báo theo ngôn ngữ người dùng đang chọn (FRD F11-S02: validation, error cũng phải dịch)
  function M(en, vi) { return LANG == "vi" ? vi : en; }

  // ---------- Lưu tạm vào trình duyệt để chuyển màn không mất ----------
  function load() {
    var base = JSON.parse(JSON.stringify(MOCK_DB));
    try {
      var saved = localStorage.getItem(STORE_KEY);
      if (saved != null) {
        var d = JSON.parse(saved);
        for (var i = 0; i < SAVED.length; i++) if (d[SAVED[i]] != null) base[SAVED[i]] = d[SAVED[i]];
      }
    } catch (e) { /* không đọc được thì dùng dữ liệu mẫu */ }
    return base;
  }
  function save() {
    var out = {};
    for (var i = 0; i < SAVED.length; i++) out[SAVED[i]] = db[SAVED[i]];
    try { localStorage.setItem(STORE_KEY, JSON.stringify(out)); } catch (e) { }
  }
  function reset() {
    try { localStorage.removeItem(STORE_KEY); } catch (e) { }
    db = load();
  }
  db = load();

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

  // ---------- Parameter Configuration (BRD 6.9): giá trị đang hiệu lực tại một thời điểm ----------
  function paramDef(key) {
    for (var i = 0; i < db.param_defs.length; i++) if (db.param_defs[i].key == key) return db.param_defs[i];
    return null;
  }
  // Phiên bản đang hiệu lực của một tham số tại thời điểm t = phiên bản mới nhất có effective_at <= t
  function activeRow(key, t) {
    var best = null;
    for (var i = 0; i < db.params.length; i++) {
      var r = db.params[i];
      if (r.key != key || r.effective_at > t) continue;
      if (!best || r.effective_at > best.effective_at || (r.effective_at == best.effective_at && r.version > best.version)) best = r;
    }
    return best;
  }
  // Bộ tham số áp dụng tại thời điểm t. parameter_version = mốc hiệu lực gần nhất, để case đã đóng giữ đúng bộ đã dùng.
  function cfgAt(t) {
    var v = {}, latest = "";
    for (var i = 0; i < db.param_defs.length; i++) {
      var r = activeRow(db.param_defs[i].key, t);
      v[db.param_defs[i].key] = r ? r.value : db.param_defs[i].value;
      if (r && r.effective_at > latest) latest = r.effective_at;
    }
    return {
      parameter_version: "ps-" + latest.replace(/[- :]/g, "").replace(/^(\d{8})(\d{4})$/, "$1-$2"),
      threshold_version: db.threshold.threshold_version, high_from: db.threshold.high_from, medium_from: db.threshold.medium_from,
      sla_calendar: v.sla_calendar,
      sla_hours: { HIGH: v.sla_hours_high, MEDIUM: v.sla_hours_medium, LOW: v.sla_hours_low },
      first_touch_hours: v.first_touch_hours,
      capacity: v.capacity, capacity_warn: v.capacity_warn, max_contact: v.max_contact, retry_gap_days: v.retry_gap_days,
      soon_hours: v.soon_hours, stale_hours: v.stale_hours, aging_days: v.aging_days,
      reopen_review_days: v.reopen_review_days, reopen_review_times: v.reopen_review_times
    };
  }
  function cfg() { return cfgAt(db.now); }

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
  function byTime(a, b) { return parseTime(a.at) - parseTime(b.at); }
  function contactsOf(id, cycle) {
    var list = [];
    for (var i = 0; i < db.contacts.length; i++) {
      var x = db.contacts[i];
      if (x.order_id == id && (cycle == null || x.cycle == cycle)) list.push(x);
    }
    return list.sort(byTime);
  }
  function cycleContacts(c) { return contactsOf(c.order_id, c.cycle_no); }
  function auditsOf(id) {
    var list = [];
    for (var i = 0; i < db.audits.length; i++) if (id == null || db.audits[i].order_id == id) list.push(db.audits[i]);
    list.sort(function (a, b) { return parseTime(b.at) - parseTime(a.at); });   // mới nhất lên đầu
    return list;
  }
  function decisionsOf(id) {
    var list = [];
    for (var i = 0; i < db.decisions.length; i++) if (db.decisions[i].order_id == id) list.push(db.decisions[i]);
    return list.sort(function (a, b) { return parseTime(b.at) - parseTime(a.at); });
  }
  function commentsOf(id) {
    var list = [];
    for (var i = 0; i < db.comments.length; i++) if (db.comments[i].order_id == id) list.push(db.comments[i]);
    return list.sort(byTime);
  }

  // ---------- Capacity (BRD 6.3) ----------
  function activeCount(userId) {
    var n = 0;
    for (var i = 0; i < db.cases.length; i++) if (db.cases[i].assignee == userId && db.cases[i].status == "IN_PROGRESS") n++;
    return n;
  }

  // ---------- SLA, aging, escalation (BRD 6.7): tính trên chu kỳ hiện tại ----------
  function slaDue(c) {
    var d = parseTime(c.queued_at);
    d.setHours(d.getHours() + cfg().sla_hours[c.risk_level]);
    return fmtTime(d);
  }
  function slaState(c) {
    if (isClosed(c)) return "none";
    var left = hoursBetween(db.now, slaDue(c));
    if (left < 0) return "over";
    if (left < cfg().soon_hours) return "soon";
    return "ok";
  }
  function agingHours(c) { return hoursBetween(c.queued_at, isClosed(c) ? c.updated_at : db.now); }
  function totalAgingHours(c) { return hoursBetween(c.original_queued_at, isClosed(c) ? c.updated_at : db.now); }
  function isEscalated(c) { return !isClosed(c) && agingHours(c) >= cfg().aging_days * 24; }
  function isStale(c) { return c.status == "IN_PROGRESS" && hoursBetween(c.updated_at, db.now) >= cfg().stale_hours; }

  // score giảm dần → gần quá SLA hơn → nằm queue lâu hơn (BRD 6.2)
  function byPriority(a, b) {
    if (b.risk_score != a.risk_score) return b.risk_score - a.risk_score;
    var sa = parseTime(slaDue(a)), sb = parseTime(slaDue(b));
    if (sa - sb != 0) return sa - sb;
    return parseTime(a.queued_at) - parseTime(b.queued_at);
  }

  // Case cần Manager ra quyết định: đã đóng mà chu kỳ này chưa có quyết định, hoặc đang mở mà đã hết lượt liên lạc
  function needsDecision(c) {
    var decided = false, ds = decisionsOf(c.order_id);
    for (var i = 0; i < ds.length; i++) if (ds[i].cycle == c.cycle_no) decided = true;
    if (decided) return false;
    if (isClosed(c)) return true;
    return c.status == "IN_PROGRESS" && cycleContacts(c).length >= cfg().max_contact;
  }

  // ---------- Định dạng trả về (API_CONTRACT mục 3) ----------
  function itemSummary(it) {
    return { product_item_id: it.product_item_id, category: it.category, risk_score: it.risk_score, risk_level: it.risk_level,
      synthetic_data_flag: it.synthetic_data_flag };
  }
  function topItem(c) {
    var best = c.items[0];
    for (var i = 1; i < c.items.length; i++) if (c.items[i].risk_score > best.risk_score) best = c.items[i];
    return best;
  }
  function orderOut(c, full) {
    var o = {};
    for (var k in c) if (k.charAt(0) != "_" && k != "assignee" && k != "items") o[k] = c[k];
    var applied = cfgAt(isClosed(c) ? c.updated_at : db.now);   // case đã đóng giữ bộ tham số lúc đóng (BRD 6.9 mục 3)
    o.case_id = "case-" + c.order_id.substring(0, 8);   // bản thật: app.review_cases.case_id (uuid)
    o.assignee_id = c.assignee || null;
    o.assignee_name = userName(c.assignee);
    o.closed_at = isClosed(c) ? c.updated_at : null;
    o.threshold_version = db.threshold.threshold_version;
    o.suggested_action = { HIGH: "CONTACT", MEDIUM: "MONITOR", LOW: "NO_ACTION" }[c.risk_level];
    o.self_claim_allowed = c.risk_level != "HIGH";   // BRD 6.3 mục 1: HIGH chỉ Manager giao
    o.outcome = c.outcome || null;
    o.skip_reason = c.skip_reason || null;
    o.parameter_version = applied.parameter_version;
    o.sla_due_at = isClosed(c) ? null : slaDue(c);
    o.sla_state = slaState(c);
    o.sla_hours_left = isClosed(c) ? null : Math.round(hoursBetween(db.now, slaDue(c)) * 100) / 100;
    o.aging_hours = Math.round(agingHours(c) * 100) / 100;
    o.total_aging_hours = Math.round(totalAgingHours(c) * 100) / 100;
    o.is_escalated = isEscalated(c);
    o.is_stale = isStale(c);
    o.stale_hours = c.status == "IN_PROGRESS" ? Math.round(hoursBetween(c.updated_at, db.now) * 100) / 100 : null;
    o.contact_count = cycleContacts(c).length;
    o.max_contact = applied.max_contact;
    o.items_count = c.items.length;
    o.top_item = itemSummary(topItem(c));
    o.has_synthetic_item = false;
    for (var i = 0; i < c.items.length; i++) if (c.items[i].synthetic_data_flag) o.has_synthetic_item = true;
    o.needs_decision = needsDecision(c);
    if (full) o.items = JSON.parse(JSON.stringify(c.items)).sort(function (a, b) { return b.risk_score - a.risk_score; });
    return o;
  }
  function contactOut(x, i) {
    return { contact_id: x.order_id.substring(0, 8) + "-c" + x.cycle + "-" + (i + 1), cycle_no: x.cycle, attempt_no: i + 1, contacted_at: x.at,
      method: x.method, result: x.result, note: x.note || "", next_contact_date: x.next_date || null,
      evidence: x.evidence || [], evidence_ref: x.evidence_ref || "",
      created_by: x.user, created_by_name: userName(x.user) };
  }
  function contactsOutAll(id) {
    // attempt_no đánh lại từ 1 trong mỗi chu kỳ (reopen reset bộ đếm, BRD 6.8)
    var all = contactsOf(id), seen = {}, out = [];
    for (var i = 0; i < all.length; i++) {
      var cy = all[i].cycle;
      seen[cy] = (seen[cy] || 0) + 1;
      out.push(contactOut(all[i], seen[cy] - 1));
    }
    return out;
  }
  var OVERRIDE_TYPES = ["REASSIGN", "REOPEN", "OVERRIDE"];
  function auditOut(e) {
    var c = e.order_id ? findCase(e.order_id) : null, over = false, count = 0;
    if (c) {
      var all = auditsOf(e.order_id);
      count = all.length;
      for (var i = 0; i < all.length; i++) if (OVERRIDE_TYPES.indexOf(all[i].type) != -1) over = true;
    }
    return { created_at: e.at, actor_id: e.actor, actor_name: userName(e.actor), order_id: e.order_id || null, event_type: e.type,
      old_value: e.old_value, new_value: e.new_value, reason: e.reason || "",
      order: c ? { status: c.status, risk_level: c.risk_level, assignee_name: userName(c.assignee), event_count: count, has_override: over } : null };
  }
  function meOut(u) {
    var n = activeCount(u.id), sp = u.role == "SPECIALIST", cf = cfg();
    return { user_id: u.id, username: u.username, full_name: u.full_name, role: u.role, preferred_language: u.preferred_language || null,
      created_at: u.created_at, active_count: sp ? n : null, capacity: cf.capacity, slots_left: sp ? Math.max(0, cf.capacity - n) : null };
  }

  // ---------- Phản hồi ----------
  function ok(body, status) { return { status: status || 200, body: body }; }
  function fail(status, code, message, details) {
    return { status: status, body: { error: { code: code, message: message, details: details || null } } };
  }
  function notFound(id) { return fail(404, "ORDER_NOT_FOUND", M("Order " + id + " was not found.", "Không tìm thấy đơn " + id + ".")); }
  function addAudit(actor, orderId, type, oldValue, newValue, reason) {
    db.audits.push({ at: tick(), actor: actor, order_id: orderId, type: type, old_value: oldValue, new_value: newValue, reason: reason || "" });
  }
  function shortId(id) { return id.substring(0, 8) + "…"; }

  // ---------- GET /orders: lọc + sắp xếp + phân trang (FRD F02, F03) ----------
  var ITEM_ID = /^[0-9a-f]{32}-\d{1,3}$/;
  function hasItem(c, itemId) {
    for (var i = 0; i < c.items.length; i++) if (c.items[i].product_item_id == itemId) return true;
    return false;
  }
  function match(c, q, me) {
    if (q.q && ITEM_ID.test(q.q) && !hasItem(c, q.q)) return false;
    if (q.q && !ITEM_ID.test(q.q) && c.order_id.indexOf(q.q) != 0) return false;
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
    if (q.needs_decision == "true" && !needsDecision(c)) return false;
    return true;
  }
  function listOrders(q, me) {
    if (q.q && !/^[0-9a-f]{1,32}$/.test(q.q) && !ITEM_ID.test(q.q)) {
      return fail(400, "INVALID_ORDER_ID", M("An order ID only contains 0-9 and a-f (at most 32 characters). A product item ID is the order ID followed by -1, -2…",
        "Mã đơn chỉ gồm 0-9 và a-f (tối đa 32 ký tự). Mã sản phẩm là mã đơn kèm -1, -2…"));
    }
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
    for (var j = offset; j < list.length && j < offset + limit; j++) {
      var o = orderOut(list[j]);
      if (q.q && ITEM_ID.test(q.q)) o.matched_item_id = q.q;
      items.push(o);
    }
    return ok({ items: items, total: list.length, limit: limit, offset: offset });
  }

  // GET /orders/summary: banner Risk Queue (F02-S01)
  function summary(me) {
    var s = { high_pending: 0, high_pending_overdue: 0, overdue: 0, escalated: 0, stale: 0, needs_decision: 0, first_pending: null };
    var list = db.cases.slice().sort(byPriority);
    for (var i = 0; i < list.length; i++) {
      var c = list[i];
      // "Đơn nên bắt đầu": đơn Pending đầu tiên mà người gọi được phép nhận (Specialist không nhận HIGH)
      if (c.status == "PENDING" && s.first_pending == null && (me.role == "MANAGER" || c.risk_level != "HIGH")) s.first_pending = orderOut(c);
      if (c.status == "PENDING" && c.risk_level == "HIGH") { s.high_pending++; if (slaState(c) == "over") s.high_pending_overdue++; }
      if (slaState(c) == "over") s.overdue++;
      if (isEscalated(c)) s.escalated++;
      if (isStale(c)) s.stale++;
      if (needsDecision(c)) s.needs_decision++;
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

  // Các chu kỳ xử lý của case: chu kỳ 1 bắt đầu lúc vào queue lần đầu, mỗi lần mở lại bắt đầu chu kỳ mới (BRD 6.8)
  function cyclesOf(c) {
    var reopens = auditsOf(c.order_id).filter(function (e) { return e.type == "REOPEN"; }).reverse();
    var out = [];
    for (var n = 1; n <= c.cycle_no; n++) {
      var start = n == 1 ? c.original_queued_at : (reopens[n - 2] ? reopens[n - 2].at : c.queued_at);
      var end = n < c.cycle_no ? (reopens[n - 1] ? reopens[n - 1].at : null) : (isClosed(c) ? c.updated_at : null);
      out.push({ cycle_no: n, started_at: start, ended_at: end, contact_count: contactsOf(c.order_id, n).length,
        parameter_version: cfgAt(end || db.now).parameter_version });
    }
    return out;
  }

  // GET /orders/{id}: chi tiết + sản phẩm + liên lạc + nhận xét + quyết định + lịch sử trạng thái + audit (chỉ Manager) (F04)
  var STATUS_EVENTS = ["CLAIM", "ASSIGN", "REASSIGN", "STATUS", "SKIP", "REOPEN", "DECISION"];
  function orderDetail(id, me) {
    var c = findCase(id);
    if (!c) return notFound(id);
    var notes = [], audits = auditsOf(id), history = [], same = 0;
    for (var i = 0; i < audits.length; i++) {
      var a = audits[i];
      if (a.type == "MODEL_NOTE") notes.push({ created_at: a.at, actor_id: a.actor, actor_name: userName(a.actor), note: a.reason });
      if (STATUS_EVENTS.indexOf(a.type) != -1) history.push({ created_at: a.at, actor_name: userName(a.actor), event_type: a.type, old_value: a.old_value, new_value: a.new_value });
    }
    history.reverse();   // cũ → mới, để vẽ dòng thời gian
    for (var j = 0; j < db.cases.length; j++) if (db.cases[j].seller_id == c.seller_id && !isClosed(db.cases[j]) && db.cases[j] != c) same++;
    var ds = decisionsOf(id).map(decisionOut);
    return ok({
      order: orderOut(c, true),
      cycles: cyclesOf(c),
      contacts: contactsOutAll(id),
      comments: commentsOf(id).map(commentOut),
      decisions: ds,
      next_step: ds.length ? { decision: ds[0].decision, next_step: ds[0].next_step, due_date: ds[0].due_date, decided_by: ds[0].actor_name, decided_at: ds[0].created_at } : null,
      status_history: history,
      model_notes: notes,
      audit_events: me.role == "MANAGER" ? audits.map(auditOut) : null,
      seller_open_count: same
    });
  }
  function commentOut(x) {
    var u = findUser(x.user);
    return { created_at: x.at, author_id: x.user, author_name: u ? u.full_name : null, author_role: u ? u.role : null, text: x.text };
  }
  function decisionOut(x) {
    return { created_at: x.at, actor_id: x.actor, actor_name: userName(x.actor), cycle_no: x.cycle, decision: x.decision,
      next_step: x.next_step, due_date: x.due_date || null, note: x.note || "" };
  }

  // ---------- Thao tác (F05–F08) ----------
  function needManager(me) { return me.role == "MANAGER" ? null : fail(403, "FORBIDDEN", M("Only managers can do this.", "Chỉ Manager được làm thao tác này.")); }

  function claim(id, me) {
    var c = findCase(id), cf = cfg();
    if (!c) return notFound(id);
    if (me.role != "SPECIALIST") return fail(403, "FORBIDDEN", M("Managers assign orders instead of claiming them.", "Manager giao đơn chứ không tự nhận."));
    if (c.status == "PENDING" && c.risk_level == "HIGH") {
      return fail(403, "HIGH_RISK_REQUIRES_ASSIGN", M("HIGH-risk orders are assigned by a manager. You can't claim this one.",
        "Đơn rủi ro HIGH do Manager giao, bạn không tự nhận được."));
    }
    if (c._conflict) {   // giả lập: người khác bấm trước một nhịp (F05-S03)
      c._conflict = false;
      c.status = "IN_PROGRESS"; c.assignee = "u1"; c.updated_at = db.now;
      db.audits.push({ at: db.now, actor: "u1", order_id: id, type: "CLAIM", old_value: "PENDING · (none)", new_value: "IN_PROGRESS · " + userName("u1"), reason: "" });
      save();
      return fail(409, "ALREADY_CLAIMED", M("Order " + shortId(id) + " was just claimed by " + userName("u1") + ".",
        "Đơn " + shortId(id) + " vừa được " + userName("u1") + " nhận trước."), { assignee_name: userName("u1") });
    }
    if (c.status != "PENDING") return fail(409, "INVALID_STATE", M("This order is no longer pending.", "Đơn này không còn ở trạng thái Chờ nhận."));
    if (activeCount(me.id) >= cf.capacity) {
      return fail(422, "CAPACITY_FULL", M("You already hold " + cf.capacity + " orders. Complete or skip one to claim more.",
        "Bạn đang giữ đủ " + cf.capacity + " đơn. Hoàn tất hoặc bỏ qua một đơn rồi mới nhận thêm."));
    }
    c.status = "IN_PROGRESS"; c.assignee = me.id; c.updated_at = tick();
    addAudit(me.id, id, "CLAIM", "PENDING · (none)", "IN_PROGRESS · " + me.full_name);
    save();
    return ok({ order: orderOut(c), me: meOut(me) });
  }

  function assign(id, body, me) {
    var deny = needManager(me); if (deny) return deny;
    var c = findCase(id), cf = cfg();
    if (!c) return notFound(id);
    var to = findUser(body.assignee_id), reason = (body.reason || "").trim(), override = !!body.override_capacity;
    if (!to || to.role != "SPECIALIST") return fail(422, "VALIDATION_ERROR", M("Choose a specialist.", "Chọn một nhân viên."), { field: "assignee_id" });
    if (isClosed(c)) return fail(409, "INVALID_STATE", M("Closed orders must be reopened before assigning.", "Đơn đã đóng phải mở lại trước khi giao."));
    var from = c.assignee;
    if (from == to.id) return fail(422, "VALIDATION_ERROR", M("That specialist is already the assignee.", "Nhân viên này đang phụ trách đơn rồi."), { field: "assignee_id" });
    if ((from != null || override) && !reason) {
      return fail(422, "REASON_REQUIRED", M("Enter a reason: reassignments and overrides are recorded in the audit log.",
        "Nhập lý do: chuyển người và vượt capacity đều được ghi vào lịch sử."), { field: "reason" });
    }
    var n = activeCount(to.id);
    if (n >= cf.capacity) {
      if (!override) return fail(422, "CAPACITY_FULL", M(to.full_name + " already holds " + cf.capacity + " orders. Tick \"Override capacity\" and enter a reason.",
        to.full_name + " đang giữ đủ " + cf.capacity + " đơn. Tích \"Vượt capacity\" và nhập lý do."));
      addAudit(me.id, id, "OVERRIDE", to.full_name + ": " + n + "/" + cf.capacity + " active", (n + 1) + "/" + cf.capacity + " (over capacity)", reason);
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

  // Minh chứng: tối đa 3 tệp, mỗi tệp ≤ 5 MB, chỉ ảnh hoặc PDF. Bản thật upload lên kho tệp, ở đây chỉ lưu tên.
  var EVIDENCE_TYPES = ["image/png", "image/jpeg", "application/pdf"];
  function addContact(id, body, me) {
    var c = findCase(id), cf = cfg();
    if (!c) return notFound(id);
    if (c.status != "IN_PROGRESS") return fail(409, "INVALID_STATE", M("Only in-progress orders can log contact attempts.", "Chỉ đơn Đang xử lý mới ghi được lần liên lạc."));
    if (c.assignee != me.id) return fail(403, "FORBIDDEN", M("Only the assignee can log contact attempts.", "Chỉ người đang phụ trách mới ghi được lần liên lạc."));
    var n = cycleContacts(c).length;
    if (n >= cf.max_contact) {
      return fail(422, "MAX_CONTACTS_REACHED", M("All " + cf.max_contact + " contact attempts are used; attempt " + (n + 1) + " is not allowed.",
        "Đã dùng hết " + cf.max_contact + " lần liên lạc, không ghi được lần " + (n + 1) + "."));
    }
    var at = (body.contacted_at || "").replace("T", " ");
    if (!at || !body.method || !body.result) return fail(422, "VALIDATION_ERROR", M("Time, method and result are required.", "Cần nhập thời điểm, phương thức và kết quả."));
    if (at > db.now) return fail(422, "VALIDATION_ERROR", M("Contact time cannot be in the future.", "Thời điểm liên lạc không được ở tương lai."), { field: "contacted_at" });
    var ev = body.evidence || [];
    if (ev.length > 3) return fail(422, "VALIDATION_ERROR", M("Attach at most 3 files.", "Đính kèm tối đa 3 tệp."), { field: "evidence" });
    for (var i = 0; i < ev.length; i++) {
      if (EVIDENCE_TYPES.indexOf(ev[i].file_type) == -1) return fail(422, "EVIDENCE_INVALID", M(ev[i].file_name + ": only PNG, JPG or PDF.", ev[i].file_name + ": chỉ nhận PNG, JPG hoặc PDF."), { field: "evidence" });
      if (ev[i].file_size > 5 * 1024 * 1024) return fail(422, "EVIDENCE_INVALID", M(ev[i].file_name + " is larger than 5 MB.", ev[i].file_name + " lớn hơn 5 MB."), { field: "evidence" });
    }
    tick();
    var x = { order_id: id, cycle: c.cycle_no, at: at, user: me.id, method: body.method, result: body.result, note: body.note || "",
      next_date: body.next_contact_date || "", evidence: ev, evidence_ref: (body.evidence_ref || "").trim() };
    db.contacts.push(x);
    c.updated_at = db.now;
    addAudit(me.id, id, "CONTACT", n + "/" + cf.max_contact, (n + 1) + "/" + cf.max_contact + " · " + body.result, "");
    save();
    return ok({ contact: contactOut(x, n), order: orderOut(c) }, 201);
  }

  function canWork(c, me) { return c.assignee == me.id || me.role == "MANAGER"; }

  function complete(id, body, me) {
    var c = findCase(id), cf = cfg();
    if (!c) return notFound(id);
    if (c.status != "IN_PROGRESS") return fail(409, "INVALID_STATE", M("Only in-progress orders can be completed.", "Chỉ đơn Đang xử lý mới hoàn tất được."));
    if (!canWork(c, me)) return fail(403, "FORBIDDEN", M("Only the assignee or a manager can complete this order.", "Chỉ người phụ trách hoặc Manager được hoàn tất đơn này."));
    var outcome = body.outcome;
    if (["HAS_ISSUE", "NO_ISSUE", "UNREACHABLE", "DUPLICATE"].indexOf(outcome) == -1) return fail(422, "VALIDATION_ERROR", M("Choose an outcome before completing.", "Chọn kết quả trước khi hoàn tất."), { field: "outcome" });
    if (outcome == "UNREACHABLE" && cycleContacts(c).length < cf.max_contact) {
      return fail(422, "OUTCOME_NOT_ALLOWED", M("\"Unreachable\" needs " + cf.max_contact + " contact attempts first.",
        "\"Không liên lạc được\" cần đủ " + cf.max_contact + " lần liên lạc trước."), { field: "outcome" });
    }
    c.status = "COMPLETED"; c.outcome = outcome; c.updated_at = tick();
    addAudit(me.id, id, "STATUS", "IN_PROGRESS", "COMPLETED · " + outcome, body.note || "");
    save();
    return ok({ order: orderOut(c) });
  }

  function skip(id, body, me) {
    var c = findCase(id);
    if (!c) return notFound(id);
    if (c.status != "IN_PROGRESS") return fail(409, "INVALID_STATE", M("Only in-progress orders can be skipped.", "Chỉ đơn Đang xử lý mới bỏ qua được."));
    if (!canWork(c, me)) return fail(403, "FORBIDDEN", M("Only the assignee or a manager can skip this order.", "Chỉ người phụ trách hoặc Manager được bỏ qua đơn này."));
    var reason = body.reason, note = (body.note || "").trim();
    if (["UNREACHABLE", "DUPLICATE", "REFUSED", "NOT_APPLICABLE", "OTHER"].indexOf(reason) == -1) return fail(422, "VALIDATION_ERROR", M("Choose a skip reason.", "Chọn lý do bỏ qua."), { field: "reason" });
    if (reason == "OTHER" && !note) return fail(422, "VALIDATION_ERROR", M("\"Other\" requires a note.", "Chọn \"Khác\" thì phải ghi chú."), { field: "note" });
    c.status = "SKIPPED"; c.skip_reason = reason; c.updated_at = tick();
    addAudit(me.id, id, "SKIP", "IN_PROGRESS", "SKIPPED", reason + (note ? ": " + note : ""));
    save();
    return ok({ order: orderOut(c) });
  }

  // Mở lại: chu kỳ mới, reset bộ đếm liên lạc và SLA; giữ lịch sử liên lạc và mốc vào queue đầu tiên (BRD 6.8)
  function reopen(id, body, me) {
    var deny = needManager(me); if (deny) return deny;
    var c = findCase(id), cf = cfg();
    if (!c) return notFound(id);
    if (!isClosed(c)) return fail(409, "INVALID_STATE", M("Only completed or skipped orders can be reopened.", "Chỉ đơn Hoàn tất hoặc Bỏ qua mới mở lại được."));
    var reason = (body.reason || "").trim();
    if (!reason) return fail(422, "REASON_REQUIRED", M("A reason is required to reopen.", "Mở lại phải có lý do."), { field: "reason" });
    var closedDays = hoursBetween(c.updated_at, db.now) / 24;
    if ((closedDays > cf.reopen_review_days || c.reopen_count >= cf.reopen_review_times) && !body.review_confirmed) {
      return fail(422, "REVIEW_CONFIRMATION_REQUIRED", M("Tick the review confirmation before reopening.", "Tích xác nhận đã xem xét trước khi mở lại."));
    }
    var old = c.status + (c.outcome ? " · " + c.outcome : (c.skip_reason ? " · " + c.skip_reason : ""));
    c.status = "PENDING"; c.assignee = null; c.outcome = null; c.skip_reason = null;
    c.reopen_count++; c.cycle_no++;
    c.queued_at = tick(); c.updated_at = db.now;
    addAudit(me.id, id, "REOPEN", old, "PENDING · cycle " + c.cycle_no, reason);
    save();
    return ok({ order: orderOut(c) });
  }

  function modelNote(id, body, me) {
    var deny = needManager(me); if (deny) return deny;
    if (!findCase(id)) return notFound(id);
    var note = (body.note || "").trim();
    if (!note) return fail(422, "VALIDATION_ERROR", M("Enter a note.", "Nhập ghi chú."), { field: "note" });
    addAudit(me.id, id, "MODEL_NOTE", "", "Flagged for model review", note);
    save();
    return ok({ created_at: db.now, actor_id: me.id, actor_name: me.full_name, note: note }, 201);
  }

  // Nhận xét: người đang phụ trách hoặc Manager
  function addComment(id, body, me) {
    var c = findCase(id);
    if (!c) return notFound(id);
    if (!(me.role == "MANAGER" || c.assignee == me.id)) {
      return fail(403, "FORBIDDEN", M("Only the assignee or a manager can comment on this order.", "Chỉ người phụ trách hoặc Manager được nhận xét đơn này."));
    }
    var text = (body.text || "").trim();
    if (!text) return fail(422, "VALIDATION_ERROR", M("Write a comment first.", "Nhập nội dung nhận xét."), { field: "text" });
    if (text.length > 1000) return fail(422, "VALIDATION_ERROR", M("Keep comments under 1,000 characters.", "Nhận xét tối đa 1.000 ký tự."), { field: "text" });
    var x = { order_id: id, at: tick(), user: me.id, text: text };
    db.comments.push(x);
    db.audits.push({ at: x.at, actor: me.id, order_id: id, type: "COMMENT", old_value: "", new_value: "Comment added", reason: text });
    save();
    return ok(commentOut(x), 201);
  }

  // Quyết định của Manager cho chu kỳ hiện tại
  var DECISIONS = ["NO_FURTHER_ACTION", "FOLLOW_UP_CUSTOMER", "WORK_WITH_SELLER", "REFER_AFTER_SALES"];
  function addDecision(id, body, me) {
    var deny = needManager(me); if (deny) return deny;
    var c = findCase(id);
    if (!c) return notFound(id);
    if (DECISIONS.indexOf(body.decision) == -1) return fail(422, "VALIDATION_ERROR", M("Choose a decision.", "Chọn quyết định."), { field: "decision" });
    var next = (body.next_step || "").trim();
    if (!next) return fail(422, "VALIDATION_ERROR", M("Write the next step so the team knows what to do.", "Ghi bước tiếp theo để nhóm biết phải làm gì."), { field: "next_step" });
    if (body.due_date && body.due_date < db.now.substring(0, 10)) return fail(422, "VALIDATION_ERROR", M("The due date can't be in the past.", "Hạn không được ở quá khứ."), { field: "due_date" });
    var x = { order_id: id, at: tick(), actor: me.id, cycle: c.cycle_no, decision: body.decision, next_step: next, due_date: body.due_date || "", note: (body.note || "").trim() };
    db.decisions.push(x);
    db.audits.push({ at: x.at, actor: me.id, order_id: id, type: "DECISION", old_value: "", new_value: body.decision, reason: next });
    save();
    return ok({ decision: decisionOut(x), order: orderOut(c) }, 201);
  }

  // ---------- Parameter Configuration (F10) ----------
  var PARAM_RULES = {
    hours: [1, 720], days: [1, 60], orders: [1, 20], times: [1, 10]
  };
  function paramsList(me) {
    var deny = needManager(me); if (deny) return deny;
    var items = [];
    for (var i = 0; i < db.param_defs.length; i++) {
      var d = db.param_defs[i], cur = activeRow(d.key, db.now), scheduled = [];
      for (var j = 0; j < db.params.length; j++) {
        var r = db.params[j];
        if (r.key == d.key && r.effective_at > db.now) scheduled.push(paramRowOut(r));
      }
      items.push({ key: d.key, unit: d.unit, in_brd: d.brd, value: cur ? cur.value : d.value, version: cur ? cur.version : 0,
        effective_at: cur ? cur.effective_at : null, updated_by_name: cur ? userName(cur.actor) : null, scheduled: scheduled });
    }
    var hist = db.params.slice().sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; }).map(paramRowOut);
    return ok({ items: items, history: hist, parameter_version: cfg().parameter_version, server_time: db.now });
  }
  function paramRowOut(r) {
    var prev = null;
    for (var i = 0; i < db.params.length; i++) if (db.params[i].key == r.key && db.params[i].version == r.version - 1) prev = db.params[i];
    return { key: r.key, version: r.version, value: r.value, old_value: prev ? prev.value : null, effective_at: r.effective_at,
      status: r.effective_at > db.now ? "SCHEDULED" : (activeRow(r.key, db.now) == r ? "ACTIVE" : "SUPERSEDED"),
      actor_id: r.actor, actor_name: userName(r.actor), reason: r.reason, created_at: r.created_at };
  }
  function changeParam(body, me) {
    var deny = needManager(me); if (deny) return deny;
    var d = paramDef(body.key);
    if (!d) return fail(422, "VALIDATION_ERROR", M("Unknown parameter.", "Không có tham số này."), { field: "key" });
    var value = body.value;
    if (d.unit == "enum") {
      if (["CALENDAR", "BUSINESS_HOURS"].indexOf(value) == -1) return fail(422, "PARAMETER_INVALID", M("Choose calendar time or business hours.", "Chọn giờ đồng hồ hoặc giờ làm việc."), { field: "value" });
    } else {
      value = +value;
      var range = PARAM_RULES[d.unit];
      if (!(value % 1 === 0) || value < range[0] || value > range[1]) {
        return fail(422, "PARAMETER_INVALID", M("Enter a whole number from " + range[0] + " to " + range[1] + ".", "Nhập số nguyên từ " + range[0] + " đến " + range[1] + "."), { field: "value" });
      }
    }
    var eff = (body.effective_at || "").replace("T", " ");
    if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(eff)) return fail(422, "VALIDATION_ERROR", M("Set when the change takes effect.", "Chọn thời điểm có hiệu lực."), { field: "effective_at" });
    if (eff < db.now) return fail(422, "PARAMETER_INVALID", M("The effective time can't be in the past.", "Thời điểm hiệu lực không được ở quá khứ."), { field: "effective_at" });
    var reason = (body.reason || "").trim();
    if (!reason) return fail(422, "REASON_REQUIRED", M("Enter a reason: every parameter change is audited.", "Nhập lý do: mọi thay đổi tham số đều được ghi lại."), { field: "reason" });
    // Ràng buộc chéo: ngưỡng cảnh báo phải nhỏ hơn capacity tại thời điểm hiệu lực
    var at = cfgAt(eff);
    if (body.key == "capacity_warn" && value >= at.capacity) return fail(422, "PARAMETER_INVALID", M("The warning level must be below capacity (" + at.capacity + ").", "Ngưỡng cảnh báo phải nhỏ hơn capacity (" + at.capacity + ")."), { field: "value" });
    if (body.key == "capacity" && value <= at.capacity_warn) return fail(422, "PARAMETER_INVALID", M("Capacity must be above the warning level (" + at.capacity_warn + ").", "Capacity phải lớn hơn ngưỡng cảnh báo (" + at.capacity_warn + ")."), { field: "value" });
    var maxV = 0, cur = activeRow(body.key, eff);
    for (var i = 0; i < db.params.length; i++) if (db.params[i].key == body.key && db.params[i].version > maxV) maxV = db.params[i].version;
    var row = { key: body.key, value: value, version: maxV + 1, effective_at: eff, actor: me.id, created_at: tick(), reason: reason };
    db.params.push(row);
    db.audits.push({ at: row.created_at, actor: me.id, order_id: null, type: "PARAMETER_CHANGE",
      old_value: body.key + " = " + (cur ? cur.value : "—"), new_value: body.key + " = " + value + " (v" + row.version + ", from " + eff + ")", reason: reason });
    save();
    return ok(paramRowOut(row), 201);
  }

  // ---------- GET /dashboard (F01): mọi số liệu tổng hợp tính ở backend ----------
  function dayList(endDay, n) {
    var out = [], d = parseTime(endDay);
    d.setDate(d.getDate() - (n - 1));
    for (var i = 0; i < n; i++) { out.push(fmtTime(d).substring(0, 10)); d.setDate(d.getDate() + 1); }
    return out;
  }
  function dashboard(q, me) {
    var deny = needManager(me); if (deny) return deny;
    var cf = cfg(), from = "";
    if (q.days) { var d0 = parseTime(db.now.substring(0, 10)); d0.setDate(d0.getDate() - (+q.days - 1)); from = fmtTime(d0).substring(0, 10); }
    var data = [];
    for (var i = 0; i < db.cases.length; i++) {
      var c = db.cases[i];
      if (from && c.queued_at.substring(0, 10) < from) continue;
      if (q.level && c.risk_level != q.level) continue;
      if (q.seller && c.seller_id != q.seller) continue;
      if (q.category && c.category != q.category) continue;
      if (q.assignee && c.assignee != q.assignee) continue;
      if (q.status && c.status != q.status) continue;
      if (q.product_item && !hasItem(c, q.product_item)) continue;
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
      var w = { user_id: usr.id, full_name: usr.full_name, active_count: activeCount(usr.id), capacity: cf.capacity,
        slots_left: Math.max(0, cf.capacity - activeCount(usr.id)), overdue: 0, stale: 0, completed: 0, has_data: false };
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
      if (["ASSIGN", "REASSIGN", "REOPEN", "OVERRIDE", "PARAMETER_CHANGE"].indexOf(ev[e].type) != -1) recent.push(auditOut(ev[e]));
    }
    // F01-S08: số case vào Risk Queue theo ngày (mốc vào queue lần đầu), tách mức rủi ro, theo cùng bộ lọc
    var days = dayList(db.now.substring(0, 10), q.days ? Math.max(+q.days, 1) : 7), trend = [];
    for (var di = 0; di < days.length; di++) trend.push({ date: days[di], HIGH: 0, MEDIUM: 0, LOW: 0 });
    for (var ti = 0; ti < data.length; ti++) {
      var idx = days.indexOf(data[ti].original_queued_at.substring(0, 10));
      if (idx != -1) trend[idx][data[ti].risk_level]++;
    }
    // Chất lượng chăm sóc: hệ thống có giúp liên hệ khách sớm, trước khi khách để lại đánh giá xấu không
    var sv = { cases: data.length, contacted: 0, reached: 0, first_in_sla: 0, first_contact_hours: [], median_first_contact_hours: null,
      issue_found: 0, issue_followed_up: 0, high_open_not_contacted: 0 };
    for (var si = 0; si < data.length; si++) {
      var sc = data[si], cl = cycleContacts(sc), all = contactsOf(sc.order_id, null);
      if (all.length) sv.contacted++;
      for (var sr = 0; sr < all.length; sr++) if (all[sr].result == "REACHED") { sv.reached++; break; }
      if (cl.length) {
        var fh = hoursBetween(sc.queued_at, cl[0].at);
        sv.first_contact_hours.push(fh);
        if (parseTime(cl[0].at) <= parseTime(slaDue(sc))) sv.first_in_sla++;
      }
      if (sc.outcome == "HAS_ISSUE") { sv.issue_found++; if (decisionsOf(sc.order_id).length) sv.issue_followed_up++; }
      if (sc.risk_level == "HIGH" && !isClosed(sc) && !cl.length) sv.high_open_not_contacted++;
    }
    if (sv.first_contact_hours.length) {
      var fs = sv.first_contact_hours.slice().sort(function (a, b) { return a - b; }), mid = Math.floor(fs.length / 2);
      sv.median_first_contact_hours = Math.round((fs.length % 2 ? fs[mid] : (fs[mid - 1] + fs[mid]) / 2) * 10) / 10;
    }
    sv.with_first_contact = sv.first_contact_hours.length;
    delete sv.first_contact_hours;

    // Việc Manager cần làm: luật cố định, xếp theo mức ảnh hưởng tới khách. Frontend chỉ hiển thị
    var actions = [], free = workload.filter(function (w) { return w.slots_left > 0; }).sort(function (a, b) { return b.slots_left - a.slots_left; });
    var best = free.length ? { user_id: free[0].user_id, full_name: free[0].full_name, slots_left: free[0].slots_left } : null;
    if (t.high_pending) actions.push({ code: "ASSIGN_HIGH", severity: t.high_pending_overdue ? "danger" : "warn", count: t.high_pending, overdue: t.high_pending_overdue, suggest: best });
    for (var wi = 0; wi < workload.length; wi++) {
      var ww = workload[wi];
      if (ww.slots_left == 0 && ww.overdue) actions.push({ code: "REBALANCE", severity: "danger", user_id: ww.user_id, full_name: ww.full_name, active: ww.active_count, capacity: ww.capacity, overdue: ww.overdue, suggest: best });
    }
    if (t.stale) actions.push({ code: "STALE", severity: "warn", count: t.stale, hours: cf.stale_hours });
    var nd = 0;
    for (var ni = 0; ni < data.length; ni++) if (needsDecision(data[ni])) nd++;
    if (nd) actions.push({ code: "DECIDE", severity: "info", count: nd });
    var topSeller = sortGroup(groups.seller)[0];
    if (topSeller && topSeller.high >= 3 && topSeller.high / topSeller.total >= 0.5)
      actions.push({ code: "SELLER_HOTSPOT", severity: "info", seller_id: topSeller.key, high: topSeller.high, total: topSeller.total, high_total: lv.HIGH });

    var out = {
      as_of: db.now, from: from || null, view: q.view == "product" ? "product" : "order", totals: t, rates: r, service: sv, actions: actions,
      by_level: [{ level: "HIGH", count: lv.HIGH }, { level: "MEDIUM", count: lv.MEDIUM }, { level: "LOW", count: lv.LOW }],
      score_bands: bandOut, by_seller: sortGroup(groups.seller), by_category: sortGroup(groups.category),
      workload: workload, attention: attention, recent_overrides: recent, trend: trend
    };
    // F01-S02/S03: góc nhìn sản phẩm. Đếm trên product item của các đơn đã lọc
    if (out.view == "product") {
      var p = { total_items: 0, HIGH: 0, MEDIUM: 0, LOW: 0, synthetic: 0, orders: data.length }, pcat = {}, items = [];
      for (var pi = 0; pi < data.length; pi++) {
        for (var pj = 0; pj < data[pi].items.length; pj++) {
          var it = data[pi].items[pj];
          p.total_items++; p[it.risk_level]++;
          if (it.synthetic_data_flag) p.synthetic++;
          var pc = pcat[it.category] || (pcat[it.category] = { key: it.category, total: 0, high: 0, open: 0, related: [] });
          pc.total++;
          if (it.risk_level == "HIGH") pc.high++;
          if (!isClosed(data[pi])) pc.open++;
          items.push({ product_item_id: it.product_item_id, order_id: data[pi].order_id, category: it.category, risk_score: it.risk_score,
            risk_level: it.risk_level, synthetic_data_flag: it.synthetic_data_flag, order_status: data[pi].status, top_factor: it.top_factors[0] || null });
        }
      }
      items.sort(function (a, b) { return b.risk_score - a.risk_score; });
      out.product = { totals: p, by_category: sortGroup(pcat), top_items: items.slice(0, 8) };
    }
    return ok(out);
  }

  function auditEvents(q, me) {
    var deny = needManager(me); if (deny) return deny;
    var ev = auditsOf(null), items = [];
    for (var i = 0; i < ev.length; i++) {
      var e = ev[i];
      if (q.event_type && e.type != q.event_type) continue;
      if (q.actor_id && e.actor != q.actor_id) continue;
      if (q.order_id && (!e.order_id || e.order_id.indexOf(q.order_id) != 0)) continue;
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
    db = load();   // trang khác có thể vừa ghi dữ liệu
    if (method == "POST" && path == "/auth/login") {
      for (var i = 0; i < db.accounts.length; i++) {
        var a = db.accounts[i];
        if (a.username == body.username && a.password == body.password) {
          return ok({ token: "mock-token-" + a.user_id, user: meOut(findUser(a.user_id)) });
        }
      }
      return fail(401, "INVALID_CREDENTIALS", M("Incorrect username or password.", "Sai tên đăng nhập hoặc mật khẩu."));
    }
    var me = userFromToken(token);
    if (!me) return fail(401, "UNAUTHENTICATED", M("Please sign in.", "Vui lòng đăng nhập."));
    if (method == "POST" && path == "/auth/logout") return { status: 204, body: null };
    if (method == "GET" && path == "/me") return ok(meOut(me));
    if (method == "PATCH" && path == "/me") {
      if (body.preferred_language != null && ["vi", "en"].indexOf(body.preferred_language) == -1) {
        return fail(422, "VALIDATION_ERROR", M("Language must be vi or en.", "Ngôn ngữ chỉ nhận vi hoặc en."), { field: "preferred_language" });
      }
      me.preferred_language = body.preferred_language;
      save();
      return ok(meOut(me));
    }
    if (method == "GET" && path == "/config") {
      var out = cfg();
      out.server_time = db.now;
      return ok(out);
    }
    if (method == "GET" && path == "/parameters") return paramsList(me);
    if (method == "POST" && path == "/parameters") return changeParam(body, me);
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
      if (method == "POST" && action == "/comments") return addComment(id, body, me);
      if (method == "POST" && action == "/decisions") return addDecision(id, body, me);
    }
    return fail(404, "NOT_FOUND", "No endpoint " + method + " " + path);
  }

  // Giả lập mạng: chậm hoặc lỗi theo ô "Giả lập trạng thái" trong khung công cụ demo
  function sim() { try { return localStorage.getItem("wf-sim") || "normal"; } catch (e) { return "normal"; } }

  function handle(method, path, query, body, token, lang) {
    var mode = sim();
    var delay = mode == "loading" ? 2500 : 120;
    return new Promise(function (resolve) {
      setTimeout(function () {
        LANG = lang == "vi" ? "vi" : "en";
        if (mode == "error" && method == "GET" && path != "/me" && path != "/config") {
          resolve(fail(500, "SERVER_ERROR", M("Simulated server error.", "Lỗi máy chủ (giả lập).")));
          return;
        }
        resolve(route(method, path, query || {}, body || {}, token));
      }, delay);
    });
  }

  return { handle: handle, reset: reset };
})();

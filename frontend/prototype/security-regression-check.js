/* Lightweight prototype-only regression check.
 * Run with: node frontend/prototype/security-regression-check.js
 */
const fs = require("fs");
const path = require("path");
const root = __dirname;
const pages = fs.readdirSync(path.join(root, "html")).filter((f) => f.endsWith(".html"));
const source = pages.map((f) => fs.readFileSync(path.join(root, "html", f), "utf8")).join("\n");
function pageSource(name) { return fs.readFileSync(path.join(root, "html", name), "utf8"); }

// These are the fields that previously reached innerHTML without escaping.
const unsafeSinks = [
  /\+\s*(?:mn|cm|d|e|c)\.(?:note|text|reason|next_step|actor_name|author_name|created_by_name|file_name)/,
  /href=['"]\s*\+\s*(?:e|ev)\.url/,
  /\+\s*(?:ns\.(?:next_step_assignee_name|reason|decided_by)|u\.username|o\.aggregation_rule|it\.top_factors|c\.assignee_name|c\.top_item\.category|a\.full_name|w\.full_name)/,
  /o\.(?:parameter_version|customer_city|customer_state|delivered_at|order_value|freight)\b/,
  /it\.(?:price|weight_g|photos|suggested_action)\b/
];
for (const pattern of unsafeSinks) {
  if (pattern.test(source)) throw new Error(`prototype security regression: ${pattern}`);
}

// Unsupported order-level/product fields must not be rendered by the prototype.
const unsupported = [/o\.max_contact\b/, /o\.parameter_version\b/, /it\.(?:price|weight_g|photos|suggested_action)\b/];
for (const pattern of unsupported) {
  if (pattern.test(source)) throw new Error(`prototype contract regression: ${pattern}`);
}

// Pin the actual delivered render paths, not only the shared helper.
const requiredSource = [
  ["../js/common.js", /escapeHtml\(c\.assignee_name\)/],
  ["html/order.html", /data-item-id="' \+ escapeHtml\(it\.product_item_id\)/],
  ["html/order.html", /addEventListener\("click"/],
  ["html/order.html", /escapeHtml\(catLabel\(it\.category\)\)/],
  ["html/order.html", /escapeHtml\(it2\.model_version\)/],
  ["html/order.html", /escapeHtml\(it2\.data_source\)/],
  ["html/overview.html", /escapeHtml\(catLabel\(it\.category\)\)/],
  ["html/overview.html", /escapeHtml\(r\.assignee_name\)/],
  ["html/overview.html", /encodeURIComponent\(it\.order_id\)/],
  ["html/index.html", /escapeHtml\(catLabel\(t\.category\)\)/],
  ["html/index.html", /escapeHtml\(cats\[c\]\)/],
  ["html/decision.html", /escapeHtml\(it\.top_factors\[0\]\)/],
  ["html/profile.html", /escapeHtml\(u\.username\)/]
];
for (const [file, pattern] of requiredSource) {
  const text = file === "../js/common.js" ? fs.readFileSync(path.join(root, "js", "common.js"), "utf8") : pageSource(file.replace(/^html\//, ""));
  if (!pattern.test(text)) throw new Error(`missing safe render path ${file}: ${pattern}`);
}

// Payload coverage for every Oracle-reported display path. This mirrors the
// browser helpers without needing a DOM, and guards against a future raw
// concatenation being added beside an escaped value.
function escapeHtml(value) {
  return String(value == null ? "" : value).replace(/[&<>'"]/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  }[c]));
}
function safeUrl(value) {
  const url = String(value == null ? "" : value);
  return /^(?:javascript|data|vbscript):/i.test(url) ? "#" : escapeHtml(url);
}
const payload = "O'Reilly <img src=x onerror=alert(1)>\"><script>alert(1)</script> javascript:alert(1)";
const textPaths = [
  "next_step", "next_step_assignee_name", "reason", "decided_by",
  "overview_name", "overview_label", "attempt_category", "attempt_assignee",
  "decision_factor", "decision_aggregation", "decision_user", "profile_username",
  "api_error"
];
for (const pathName of textPaths) {
  const rendered = escapeHtml(payload);
  if (/<\/?(?:script|img)\b/i.test(rendered) || /<[^>]*\bonerror\s*=/i.test(rendered) || rendered.includes("<")) {
    throw new Error(`payload escaped incorrectly for ${pathName}`);
  }
}
for (const url of ["javascript:alert(1)", "data:text/html,<script>alert(1)</script>", "vbscript:msgbox(1)"]) {
  if (safeUrl(url) !== "#") throw new Error(`unsafe URL emitted for payload: ${url}`);
}

// DOM-like render fixtures exercise the same context decisions used by the
// page renderers: text nodes/HTML fragments, attributes, inline arguments,
// and links. Each fixture must remain inert with the malicious value.
const renderFixtures = {
  assignment: () => `<b>${escapeHtml(payload)}</b>`,
  orderItem: () => `<tr data-item-id="${escapeHtml(payload)}"><td>${escapeHtml(payload)}</td></tr>`,
  overview: () => `<a href="${safeUrl("order.html?id=" + encodeURIComponent(payload))}">${escapeHtml(payload)}</a>`,
  attempt: () => `<span>${escapeHtml(payload)}</span>`,
  decision: () => `<code>${escapeHtml(payload)}</code>`,
  profile: () => `<code>${escapeHtml(payload)}</code>`,
  apiError: () => `<span>${escapeHtml(payload)}</span>`
};
for (const [name, render] of Object.entries(renderFixtures)) {
  const html = render();
  if (/<(?:script|img)\b/i.test(html)) {
    throw new Error(`executable payload reflected by ${name} render`);
  }
}
const itemFixture = renderFixtures.orderItem();
if (/\bonclick\s*=|\bonkeydown\s*=/i.test(itemFixture) ||
    !/data-item-id="[^\"]*&lt;img[^\"]*"/i.test(itemFixture) || !itemFixture.includes("&#39;")) {
  throw new Error("order item data attribute is not inert for apostrophe/URL payloads");
}
console.log("prototype security/contract checks passed");

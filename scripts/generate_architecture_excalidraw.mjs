// Generates docs/system-architecture.excalidraw (+ SVG preview) in a logo-first,
// numbered-flow style. Run from repo root: node scripts/generate_architecture_excalidraw.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const output = resolve("docs/system-architecture.excalidraw");
const previewOutput = resolve("docs/system-architecture-preview.svg");
const W = 2000;
const H = 1150;
const elements = [];
const files = {};
let seed = 4100;
let index = 0;

const C = {
  ink: "#1e1e1e",
  muted: "#64748b",
  green: "#2f9e44",
  blue: "#1971c2",
  orange: "#e8590c",
  violet: "#7048e8",
  teal: "#0c8599",
  hatch: "#e7f5ff",
};

function common(id, type, x, y, width, height) {
  return {
    id, type, x, y, width, height, angle: 0,
    strokeColor: C.ink, backgroundColor: "transparent", fillStyle: "solid",
    strokeWidth: 2, strokeStyle: "solid", roughness: 1, opacity: 100,
    groupIds: [], frameId: null, index: `a${String(index++).padStart(4, "0")}`,
    roundness: type === "rectangle" ? { type: 3 } : null,
    seed: seed++, version: 1, versionNonce: seed * 13, isDeleted: false,
    boundElements: [], updated: 1793149200000, link: null, locked: false,
  };
}

function text(id, x, y, width, value, o = {}) {
  const fontSize = o.size ?? 16;
  const lines = value.split("\n").length;
  const t = common(id, "text", x, y, width, lines * fontSize * 1.25);
  Object.assign(t, {
    strokeColor: o.color ?? C.ink, strokeWidth: 1, roughness: 0,
    fontSize, fontFamily: 5, text: value, originalText: value,
    textAlign: o.align ?? "center", verticalAlign: "top", containerId: null,
    autoResize: false, lineHeight: 1.25,
  });
  elements.push(t);
}

function icon(id, name, x, y, size = 52) {
  const fileId = `logo-${name}`;
  if (!files[fileId]) {
    const svg = readFileSync(resolve(`docs/assets/architecture-icons/${name}.svg`));
    files[fileId] = {
      id: fileId, mimeType: "image/svg+xml",
      dataURL: `data:image/svg+xml;base64,${svg.toString("base64")}`,
      created: 1793149200000, lastRetrieved: 1793149200000,
    };
  }
  const img = common(id, "image", x, y, size, size);
  Object.assign(img, { fileId, status: "saved", scale: [1, 1], crop: null });
  elements.push(img);
}

// Logo node: one or more logos centred on cx, caption underneath.
function node(id, logos, cx, y, caption, o = {}) {
  const size = o.size ?? 52;
  const gap = 10;
  const total = logos.length * size + (logos.length - 1) * gap;
  logos.forEach((name, i) => icon(`${id}-${name}`, name, cx - total / 2 + i * (size + gap), y, size));
  text(`${id}-cap`, cx - 110, y + size + 6, 220, caption, { size: o.capSize ?? 15 });
}

function rect(id, x, y, w, h, o = {}) {
  const r = common(id, "rectangle", x, y, w, h);
  Object.assign(r, {
    strokeColor: o.color ?? C.ink, backgroundColor: o.fill ?? "transparent",
    fillStyle: o.fillStyle ?? "solid", strokeStyle: o.dash ? "dashed" : "solid",
    strokeWidth: o.width ?? 2, roughness: o.rough ?? 1,
  });
  elements.push(r);
}

function ellipse(id, x, y, w, h, color = C.ink) {
  const e = common(id, "ellipse", x, y, w, h);
  e.strokeColor = color;
  e.backgroundColor = "#ffffff";
  elements.push(e);
}

function actor(id, cx, y, label) {
  ellipse(`${id}-head`, cx - 12, y, 24, 24);
  ellipse(`${id}-body`, cx - 22, y + 26, 44, 34);
  text(`${id}-cap`, cx - 80, y + 64, 160, label, { size: 15 });
}

// Cluster in the template style: rounded green border, logo badge + title.
function cluster(id, x, y, w, h, title, logo, o = {}) {
  rect(id, x, y, w, h, { color: o.color ?? C.green, dash: o.dash, fill: o.fill, fillStyle: o.fill ? "hachure" : "solid" });
  if (logo) icon(`${id}-badge`, logo, x - 14, y - 40, 40);
  text(`${id}-title`, x + 34, y - 32, w - 40, title, { size: 18, align: "left", color: C.ink });
}

// Arrow through points [[x,y],...]; label placed at `at` (defaults to mid of first segment).
function arrow(id, pts, label, o = {}) {
  const [x0, y0] = pts[0];
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  const a = common(id, "arrow", x0, y0, Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys));
  Object.assign(a, {
    strokeColor: o.color ?? C.ink, strokeStyle: o.dash ? "dashed" : "solid",
    points: pts.map(([x, y]) => [x - x0, y - y0]), lastCommittedPoint: null,
    startBinding: null, endBinding: null, startArrowhead: o.both ? "arrow" : null,
    endArrowhead: "arrow", roundness: null,
  });
  elements.push(a);
  if (label) {
    const [lx, ly] = o.at ?? [(pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2 - 9];
    const lw = label.length * 7.2 + 14;
    rect(`${id}-label-bg`, lx - lw / 2, ly - 2, lw, 21, { color: "transparent", fill: "#ffffff", rough: 0 });
    text(`${id}-label`, lx - lw / 2, ly, lw, label, { size: 13, color: o.color ?? C.ink });
  }
}

// ---------------------------------------------------------------- title
text("title", 40, 24, 1200, "Hidden Dissatisfaction — System Architecture", { size: 30, align: "left" });
text("subtitle", 40, 64, 1500, "Product-item risk scoring → order queue for human review", { size: 16, align: "left", color: C.muted });

// Layout rule: every logo in a row shares one centre line (row 1: y=255, row 2: y=640,
// row 3: y=985) so flow arrows stay straight; cross-row links are orthogonal and nested
// (2.2 outside 2.3, 3.4 on its own lane) so no two lines cross.

// ---------------------------------------------------------------- row 1: runtime
actor("specialist", 80, 222, "Specialist /\nManager");

cluster("fe", 190, 150, 370, 220, "Frontend", "docker");
node("nginx", ["nginx"], 285, 231, "NGINX\nstatic + /api proxy", { size: 48 });
node("angular", ["angular"], 475, 231, "Angular SPA\nqueue · decision", { size: 48 });
arrow("a11", [[115, 255], [258, 255]], "1.1 open", { color: C.green });
arrow("a12", [[312, 255], [448, 255]], "1.2 SPA", { color: C.green });
arrow("a13", [[502, 255], [662, 255]], "1.3 REST", { color: C.green, at: [600, 246] });

cluster("be", 640, 150, 620, 220, "Backend API", "docker");
node("api", ["fastapi", "pydantic", "jsonwebtokens"], 735, 235, "FastAPI /api/v1\nschemas · JWT", { size: 40 });
rect("core", 870, 225, 190, 60, { color: C.orange, fill: "#fff4e6", rough: 0 });
text("core-t", 870, 236, 190, "Application + domain\nuse cases · policies", { size: 15, color: C.orange });
node("orm", ["sqlalchemy"], 1165, 231, "SQLAlchemy\nadapters", { size: 48 });
arrow("a14", [[807, 255], [868, 255]], "1.4", { color: C.green });
arrow("a15", [[1062, 255], [1138, 255]], "port", { color: C.green });

cluster("db", 1330, 150, 360, 220, "Storage", "docker");
node("pg", ["postgresql"], 1440, 230, "PostgreSQL\nbronze → gold · ml · app", { size: 50 });
node("evidence", ["volume"], 1610, 231, "Evidence\nvolume", { size: 48 });
arrow("a16", [[1192, 255], [1412, 255]], "1.5 SQL", { color: C.green, at: [1295, 246] });
arrow("a17", [[685, 233], [685, 185], [1610, 185], [1610, 229]], "1.6 upload evidence", { color: C.violet, dash: true, at: [1170, 176] });

cluster("ci", 1760, 150, 200, 220, "CI", "githubactions", { color: C.violet });
node("gha", ["githubactions"], 1860, 205, "GitHub Actions", { size: 48 });
["ruff", "pytest", "eslint"].forEach((name, i) => icon(`ci-${name}`, name, 1803 + i * 42, 300, 30));
text("ci-t", 1770, 340, 180, "lint · types · tests", { size: 14, color: C.muted });

// ---------------------------------------------------------------- row 2: data + ML jobs
cluster("pipe", 190, 560, 990, 270, "Data pipeline", "docker", { color: C.blue, dash: true, fill: C.hatch });
node("csv", ["csv"], 270, 617, "Olist raw\n9 CSV files", { size: 46 });
node("ingest", ["python"], 490, 617, "CLI ingest\nSHA-256 → Bronze", { size: 46 });
node("dbt", ["dbt"], 740, 617, "dbt build\nSilver → Gold", { size: 46 });
node("feat", ["postgresql", "apacheparquet"], 1010, 618, "gold features\n→ parquet", { size: 44 });
arrow("a21", [[296, 640], [464, 640]], "2.1 validate", { color: C.blue });
arrow("a22", [[490, 615], [490, 440], [1400, 440], [1400, 335]], "2.2 load Bronze", { color: C.blue, at: [700, 431] });
arrow("a23", [[740, 615], [740, 465], [1440, 465], [1440, 335]], "2.3 transform in-db", { color: C.blue, dash: true, both: true, at: [1000, 456] });
arrow("a24", [[766, 640], [958, 640]], "2.4 export", { color: C.blue });

cluster("ml", 1270, 560, 690, 270, "ML training & scoring", "python", { color: C.orange, dash: true, fill: "#fff4e6" });
node("train", ["pandas", "scikitlearn", "catboost"], 1385, 620, "train\ntemporal split · calibrate", { size: 40 });
node("artifact", ["artifact"], 1600, 616, "model artifact\njoblib + metrics", { size: 48 });
node("score", ["python"], 1860, 617, "score → max-v1\norder risk queue", { size: 46 });
arrow("a31", [[1061, 640], [1312, 640]], "3.1 train", { color: C.orange, at: [1225, 631] });
arrow("a32", [[1457, 640], [1574, 640]], "3.2 save", { color: C.orange });
arrow("a33", [[1626, 640], [1835, 640]], "3.3 load", { color: C.orange });
arrow("a34", [[1860, 615], [1860, 452], [1480, 452], [1480, 335]], "3.4 write predictions", { color: C.orange, at: [1670, 443] });

// ---------------------------------------------------------------- row 3: dev + legend
cluster("dev", 190, 900, 700, 210, "Development environment", "uv", { color: C.ink });
actor("ds", 270, 952, "Data Scientist");
node("jupyter", ["jupyter"], 520, 961, "Jupyter\nEDA · experiments", { size: 48 });
node("uvpy", ["uv", "python"], 760, 963, "uv · Python 3.11\nfrozen uv.lock", { size: 44 });
arrow("ds-j", [[300, 985], [494, 985]], "research", { color: C.orange });
arrow("j-feat", [[520, 959], [520, 860], [1010, 860], [1010, 715]], "read snapshot", { color: C.orange, dash: true, at: [770, 851] });

cluster("legend", 1270, 900, 690, 210, "Legend", null, { color: C.muted });
[
  [C.green, false, "1.x  online request (specialist / manager)"],
  [C.blue, false, "2.x  data pipeline: CSV → Bronze → Silver → Gold"],
  [C.orange, false, "3.x  training & scoring (manual jobs)"],
  [C.ink, true, "dashed = in-db / file / read-only link · no secrets shown"],
].forEach(([color, dash, label], i) => {
  const y = 945 + i * 40;
  arrow(`lg${i}`, [[1300, y], [1380, y]], null, { color, dash });
  text(`lg${i}-t`, 1400, y - 10, 540, label, { size: 15, align: "left" });
});

// ---------------------------------------------------------------- write scene
writeFileSync(output, `${JSON.stringify({
  type: "excalidraw", version: 2, source: "https://github.com/excalidraw/excalidraw",
  elements,
  appState: { gridSize: null, viewBackgroundColor: "#ffffff", currentItemFontFamily: 5 },
  files,
}, null, 2)}\n`, "utf8");

// ---------------------------------------------------------------- SVG preview
// ponytail: flat preview for docs/README; open the .excalidraw for the hand-drawn look.
const xml = (v) => String(v).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const colors = [...new Set(elements.filter((e) => e.type === "arrow").map((e) => e.strokeColor))];
const markerId = (c) => `m${c.slice(1)}`;

function preview(e) {
  const dash = e.strokeStyle === "dashed" ? ' stroke-dasharray="9 7"' : "";
  if (e.type === "rectangle") {
    const fill = e.backgroundColor === "transparent" ? "none" : e.backgroundColor;
    const op = e.fillStyle === "hachure" ? ' fill-opacity="0.55"' : "";
    return `<rect x="${e.x}" y="${e.y}" width="${e.width}" height="${e.height}" rx="14" fill="${fill}"${op} stroke="${e.strokeColor}" stroke-width="${e.strokeWidth}"${dash}/>`;
  }
  if (e.type === "ellipse") {
    return `<ellipse cx="${e.x + e.width / 2}" cy="${e.y + e.height / 2}" rx="${e.width / 2}" ry="${e.height / 2}" fill="#fff" stroke="${e.strokeColor}" stroke-width="2"/>`;
  }
  if (e.type === "arrow") {
    const pts = e.points.map(([x, y]) => `${e.x + x},${e.y + y}`).join(" ");
    const start = e.startArrowhead ? ` marker-start="url(#${markerId(e.strokeColor)})"` : "";
    return `<polyline points="${pts}" fill="none" stroke="${e.strokeColor}" stroke-width="2"${dash} marker-end="url(#${markerId(e.strokeColor)})"${start}/>`;
  }
  if (e.type === "image") {
    return `<image href="${files[e.fileId].dataURL}" x="${e.x}" y="${e.y}" width="${e.width}" height="${e.height}"/>`;
  }
  if (e.type === "text") {
    const anchor = { center: "middle", right: "end" }[e.textAlign] ?? "start";
    const tx = e.textAlign === "center" ? e.x + e.width / 2 : e.x;
    const spans = e.text.split("\n").map((l, i) => `<tspan x="${tx}" dy="${i ? e.fontSize * 1.25 : 0}">${xml(l || " ")}</tspan>`).join("");
    return `<text x="${tx}" y="${e.y + e.fontSize}" fill="${e.strokeColor}" font-family="Segoe Print, Comic Sans MS, sans-serif" font-size="${e.fontSize}" text-anchor="${anchor}">${spans}</text>`;
  }
  return "";
}

const markers = colors.map((c) => `<marker id="${markerId(c)}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="${c}"/></marker>`).join("");
writeFileSync(previewOutput, `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>${markers}</defs><rect width="${W}" height="${H}" fill="#fff"/>
${elements.map(preview).join("\n")}
</svg>\n`, "utf8");

console.log(`Wrote ${output} (${elements.length} elements) and ${previewOutput}`);

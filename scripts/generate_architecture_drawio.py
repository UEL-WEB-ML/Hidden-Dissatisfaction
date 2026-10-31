"""Generate docs/system-architecture.drawio from one coordinate model.

Run from repo root:  python scripts/generate_architecture_drawio.py [--preview out.svg]
All coordinates below are absolute; children of containers are converted to relative
geometry on write, so groups stay draggable in draw.io. Logos are embedded (offline).
"""

import base64
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

ICONS = Path("docs/assets/architecture-icons")
OUT = Path("docs/system-architecture.drawio")

GREEN, BLUE, ORANGE, VIOLET, INK, MUTED, RED = (
    "#2f9e44", "#1971c2", "#e8590c", "#7048e8", "#1e1e1e", "#64748b", "#e03131")
FONT = "fontFamily=Comic Sans MS;"

cells: list[dict] = []
absolute: dict[str, tuple[float, float, float, float]] = {}


def _icon(name: str) -> str:
    data = base64.b64encode((ICONS / f"{name}.svg").read_bytes()).decode()
    return f"data:image/svg+xml,{data}"


def _add(cid, style, x, y, w, h, value="", parent=None, kind="vertex"):
    absolute[cid] = (x, y, w, h)
    cells.append(dict(id=cid, style=style, x=x, y=y, w=w, h=h, value=value,
                      parent=parent, kind=kind))


def group(cid, x, y, w, h, title, color=GREEN, badge="docker", dashed=False,
          fill="none", parent=None, size=16):
    style = (f"rounded=1;arcSize=2;whiteSpace=wrap;html=1;container=1;collapsible=0;"
             f"strokeColor={color};fillColor={fill};strokeWidth=2;{FONT}"
             f"verticalAlign=top;align=left;spacingLeft={44 if badge else 10};spacingTop=4;"
             f"fontSize={size};fontStyle=1;{'dashed=1;' if dashed else ''}")
    _add(cid, style, x, y, w, h, title, parent)
    if badge:
        image(f"{cid}-badge", badge, x + 8, y + 5, 30, parent=cid)


def box(cid, x, y, w, h, label, parent, color=INK, fill="#ffffff", size=11,
        dashed=False, align="center", valign="middle", extra=""):
    style = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;strokeColor={color};"
             f"fillColor={fill};fontSize={size};{FONT}align={align};verticalAlign={valign};"
             f"spacing=4;{'dashed=1;' if dashed else ''}{extra}")
    _add(cid, style, x, y, w, h, label, parent)


def image(cid, name, x, y, s, label="", parent=None, size=11):
    style = (f"shape=image;html=1;imageAspect=1;aspect=fixed;image={_icon(name)};"
             f"verticalLabelPosition=bottom;verticalAlign=top;labelBackgroundColor=none;"
             f"fontSize={size};{FONT}")
    _add(cid, style, x, y, s, s, label, parent)


def note(cid, x, y, w, h, label, parent=None, color=INK, size=11, align="center"):
    style = (f"text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;"
             f"align={align};verticalAlign=middle;fontSize={size};fontColor={color};{FONT}")
    _add(cid, style, x, y, w, h, label, parent)


def icon_box(cid, x, y, w, h, icon, label, parent, color=INK, fill="#ffffff", s=24, size=11):
    box(cid, x, y, w, h, label, parent, color=color, fill=fill, align="left", size=size,
        extra=f"spacingLeft={s + 10};")
    image(f"{cid}-i", icon, x + 6, y + (h - s) / 2, s, parent=parent)


def edge(cid, src, tgt, label="", color=INK, dashed=False, pts=(), exit=(1, .5),
         entry=(0, .5), both=False, size=10):
    style = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor={color};"
             f"strokeWidth=2;fontColor={color};fontSize={size};{FONT}"
             f"labelBackgroundColor=#ffffff;endArrow=block;endFill=1;"
             f"{'startArrow=block;startFill=1;' if both else ''}{'dashed=1;' if dashed else ''}"
             f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
             f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;")
    cells.append(dict(id=cid, style=style, value=label, kind="edge", src=src, tgt=tgt,
                      pts=list(pts), exit=exit, entry=entry))


# ====================================================================== title
note("title", 20, 12, 900, 44, "<b>Hidden Dissatisfaction – System Architecture</b>",
     size=30, align="left")
note("subtitle", 20, 56, 900, 28, "Online human-review workflow + Offline data/ML pipeline",
     size=18, align="left")

# ====================================================================== 1. web flow
group("web", 18, 112, 655, 703, "Web / Online Review Flow", size=18)
icon_box("ls", 193, 160, 220, 66, "volume",
         "Browser localStorage<br>hd_access_token (JWT)<br>hd_language", "web", s=30)
image("spec", "person", 55, 240, 44, "<b>Specialist</b><br>(review &amp; contact)", "web")
image("mgr", "person", 55, 368, 44, "<b>Manager</b><br>(oversee &amp; assign)", "web")
box("ng", 169, 296, 128, 98, "<br><br><b>Angular SPA</b><br>(Frontend)", "web", size=12)
image("ng-i", "angular", 213, 303, 40, parent="web")
note("ng-n", 150, 398, 166, 52, "authGuard / managerGuard /<br>facades / stores", "web", size=10)
box("nginx", 383, 296, 92, 98, "<br><br><br><b>NGINX</b>", "web", size=12)
image("nginx-i", "nginx", 409, 307, 40, parent="web")
note("nginx-n", 360, 398, 138, 36, "serve SPA +<br>proxy /api", "web", size=10)
box("fapi", 527, 296, 126, 98, "<br><br><br><b>FastAPI</b>", "web", size=12)
image("fapi-i", "fastapi", 570, 307, 40, parent="web")
note("fapi-n", 505, 398, 170, 36, "auth, role check,<br>routes, DTO mapping", "web", size=10)

group("screens", 36, 478, 625, 195, "Key Screens / Features (Angular)", color=MUTED,
      badge=None, dashed=True, parent="web", size=13)
screens = [("lock", "<b>Login</b>"), ("chart", "<b>Dashboard</b><br>(Manager read-only)"),
           ("list", "<b>Queue</b><br>GET /orders<br>/orders/summary<br>/orders/filter-options"),
           ("doc", "<b>Order Detail</b><br>(view risk, history)"),
           ("phone", "<b>Attempt</b><br>(contact + evidence)"),
           ("check", "<b>Decisions</b><br>(workspace)"), ("clock", "<b>Audit</b><br>(view history)"),
           ("gear", "<b>Parameters</b><br>(Manager only)")]
for i, (ic, label) in enumerate(screens):
    icon_box(f"sc{i}", 50 + (i % 4) * 152, 512 + (i // 4) * 80, 142, 70, ic, label,
             "screens", color=INK)

group("actions", 36, 686, 625, 117, "Key Actions / Rules", color=MUTED, badge=None,
      dashed=True, parent="web", size=13)
actions = [("person", "<b>Claim Order</b><br>(Specialist only)<br>LOW / MEDIUM<br>capacity check"),
           ("people", "<b>Assign / Reassign</b><br>(Manager only;<br>HIGH risk)"),
           ("check", "<b>Complete / Skip</b><br>(update status)"),
           ("clip", "<b>Contact Attempt</b><br>+ evidence file")]
for i, (ic, label) in enumerate(actions):
    icon_box(f"ac{i}", 50 + i * 152, 718, 142, 76, ic, label, "actions",
             color="#f08c00", fill="#fff9db")

# ====================================================================== 2. app/domain/infra
group("layers", 684, 105, 590, 385, "Application / Domain / Infrastructure", size=18)
columns = [
    ("app", 704, "<b>Application Layer</b><br>(Use Cases / Commands / Reads)",
     ["Review Use Cases", "Query Use Cases", "DTO Mapping", "Permission &amp; Role Check"]),
    ("dom", 893, "<b>Domain Layer</b><br>(Policies / State Machine)",
     ["Case State Machine", "Business Rules<br>(capacity, contact limit, SLA)",
      "Domain Entities<br>(Order, Attempt, Decision, …)", "Domain Services"]),
    ("inf", 1082, "<b>Infrastructure Layer</b><br>(PostgreSQL Adapters)",
     ["Repositories (Transaction)", "Publish Audit Events<br>(in same transaction)",
      "Read ML Projections<br>(item/order risk)", "Local Evidence Store"]),
]
for cid, x, title, items in columns:
    box(cid, x, 150, 177, 262, title, "layers", valign="top", size=11)
    for j, item in enumerate(items):
        box(f"{cid}{j}", x + 10, 200 + j * 52, 157, 42, item, "layers", size=10)
box("n-read", 728, 424, 210, 48, "Online API reads ML projections +<br>application workflow state",
    "layers", color="#f08c00", fill="#fff9db", size=10)
box("n-write", 1050, 424, 190, 48, "Workflow writes + audit<br>together in one transaction",
    "layers", color="#f08c00", fill="#fff9db", size=10)

# ====================================================================== 3. operational DB
group("db", 684, 508, 590, 307, "Operational Database (PostgreSQL)", badge="postgresql",
      size=18)
group("appschema", 700, 548, 318, 222,
      "app schema <font style='font-size:10px'>(workflow state)</font>", color=BLUE,
      badge=None, dashed=True, parent="db", size=14)
app_tables = ["review_cases", "review_cycles", "assignments", "contact_attempts",
              "case_comments", "manager_decisions", "audit_events", "parameters", "users"]
for i, t in enumerate(app_tables):
    icon_box(f"t{i}", 710 + (i % 3) * 102, 584 + (i // 3) * 60, 96, 48, "table", t,
             "appschema", s=16, size=9)
group("mlschema", 1030, 548, 232, 222,
      "ml schema <font style='font-size:10px'>(model outputs – read only)</font>",
      color=VIOLET, badge=None, dashed=True, parent="db", size=14)
icon_box("ip", 1042, 588, 208, 70, "table",
         "<b>item_prediction_scores</b><br>(item_id, risk, score)", "mlschema", s=26)
icon_box("op", 1042, 676, 208, 80, "table",
         "<b>order_prediction_scores</b><br>(order_id, risk_level, score,<br>risk_queue projection)",
         "mlschema", s=26)

# ====================================================================== 4. offline pipeline
group("pipe", 1288, 105, 692, 708, "Offline Data / ML Pipeline", size=18)
box("n-optin", 1722, 112, 248, 44,
    "Explicit opt-in jobs; API startup<br>does not auto ingest / train / score", "pipe",
    color=BLUE, size=10)
image("csv", "csv", 1302, 170, 50, "9 Olist CSV Files", "pipe")
image("manifest", "doc", 1430, 172, 46, "Bronze Manifest<br>(filename + header +<br>SHA-256)", "pipe")
image("bronze-pg", "postgresql", 1550, 168, 50, "PostgreSQL<br>Bronze Snapshot", "pipe")
group("dbt", 1640, 166, 330, 122, "", color=RED, badge=None, dashed=True, fill="#fff5f5",
      parent="pipe")
image("dbt-i", "dbt", 1760, 172, 34, parent="dbt")
note("dbt-t", 1798, 172, 60, 34, "<b>dbt</b>", "dbt", size=18)
for i, layer in enumerate(["Bronze", "Silver", "Intermediate", "Gold"]):
    image(f"L{i}", "volume", 1662 + i * 80, 218, 32, layer, "dbt", size=10)
icon_box("gold", 1420, 348, 236, 52, "table", "<b>gold.ml_modelling_items</b><br>(curated dataset)",
         "pipe", color=INK, s=26)
icon_box("parq", 1736, 348, 232, 52, "apacheparquet", "Export modelling_items.parquet",
         "pipe", color=INK, s=28)

group("train", 1304, 418, 664, 160, "Model Training &amp; Selection", color=ORANGE,
      badge=None, dashed=True, fill="#fff4e6", parent="pipe", size=14)
image("pandas", "pandas", 1400, 448, 40, "pandas", "train")
image("sk", "scikitlearn", 1590, 446, 44, "scikit-learn", "train")
image("cb", "catboost", 1790, 448, 40, "CatBoost", "train")
box("t-temporal", 1322, 520, 176, 46, "Temporal training<br>/ model selection", "train")
box("t-cal", 1560, 520, 150, 46, "Calibration +<br>threshold", "train")
icon_box("t-art", 1762, 520, 196, 46, "artifact", "Versioned model artifact<br>+ metrics + selection record",
         "train", s=24)

group("score", 1304, 594, 664, 132, "Scoring &amp; Release", color=ORANGE, badge=None,
      dashed=True, fill="#fff4e6", parent="pipe", size=14)
icon_box("s-rel", 1318, 636, 150, 54, "python", "Release scoring<br>(batch job)", "score", s=28)
icon_box("s-max", 1490, 636, 150, 54, "gear", "max-v1<br>aggregation by order", "score", s=28)
icon_box("s-write", 1662, 636, 170, 54, "postgresql",
         "Write item predictions<br>+ order risk (ml schema)", "score", s=28)
icon_box("s-queue", 1848, 630, 110, 66, "chart", "Risk queue<br>source for<br>online system",
         "score", s=24)

# ====================================================================== 5. evidence
group("evid", 18, 868, 385, 236, "Evidence File Storage", color=GREEN, size=16)
icon_box("vol", 52, 950, 184, 76, "volume",
         "<b>Evidence File Volume</b><br>(Docker volume<br>evidence_data)", "evid", s=34)
note("tree", 244, 940, 152, 70,
     "evidence/{yyyy}/{mm}/<br>&nbsp;└─ {uuid}.{png|jpg|pdf}<br>max 3 files · 5 MB", "evid",
     size=10, align="left")
note("tree-n", 200, 1046, 196, 40, "Store file metadata<br>and link to attempt", "evid", size=10)

# ====================================================================== 6. audit
group("audit", 418, 862, 624, 242, "Audit &amp; Governance", badge="doc", size=16)
box("ae", 440, 908, 292, 132, "", "audit", dashed=True)
image("ae-i", "doc", 452, 950, 40, parent="audit")
note("ae-t", 500, 912, 228, 126,
     "<b>Audit Events (immutable)</b><br>• claim, assign, contact, complete,<br>"
     "• skip, reopen, comment,<br>• model note, decision,<br>• parameter change, queue seed",
     "audit", size=10, align="left")
box("pc", 752, 908, 276, 160, "", "audit", dashed=True)
image("pc-i", "gear", 764, 920, 30, parent="audit")
note("pc-t", 800, 912, 222, 152,
     "<b>Parameter Configuration</b><br>(Manager only, versioned bundles)<br>"
     "• capacity (max concurrent cases)<br>• max_contact (attempt limit)<br>"
     "• SLA hours by risk level<br>• reopen review days / times<br>"
     "• aging / stale / soon hours", "audit", size=10, align="left")
note("pc-n", 760, 1068, 260, 30, "Parameters affect workflow rules and capacity", "audit",
     size=10)

# ====================================================================== 7. state machine
group("sm", 1056, 832, 428, 272, "Case State Machine", badge="docker", size=16)
box("st-p", 1210, 868, 116, 46, "<b>PENDING</b><br>(new / reopened)", "sm", fill="#f1f3f5")
box("st-i", 1084, 940, 118, 46, "<b>IN_PROGRESS</b><br>(contacting)", "sm", color=BLUE,
    fill="#e7f5ff")
box("st-c", 1300, 940, 120, 46, "<b>COMPLETED</b><br>(outcome)", "sm", color=GREEN,
    fill="#ebfbee")
box("st-s", 1210, 1004, 116, 46, "<b>SKIPPED</b><br>(reason / unreachable)", "sm",
    color=RED, fill="#fff5f5")
box("st-n", 1076, 1060, 388, 38,
    "Workflow can change assignment / status / comments / contacts / decisions,<br>"
    "but cannot edit score / risk level.", "sm", color="#f08c00", fill="#fff9db", size=10)

# ====================================================================== 8. compose + legend
group("compose", 1494, 832, 486, 154, "Docker Compose Runtime", size=16)
box("startup", 1508, 870, 460, 106, "", "compose")
note("startup-t", 1516, 872, 120, 20, "Startup order:", "compose", align="left")
runtime = [("postgresql", "postgres<br>(database)"), ("gear", "migrate<br>(psql V001–V009)"),
           ("fastapi", "API<br>(backend)"), ("angular", "frontend<br>(Angular SPA)")]
for i, (ic, label) in enumerate(runtime):
    image(f"rt{i}", ic, 1548 + i * 112, 892, 38, label, "compose", size=10)

group("legend", 1494, 998, 486, 106, "Arrow / Flow Legend", color=MUTED, badge=None,
      dashed=True, size=12)
legend = [(GREEN, False, "User-facing online request (HTTP)"),
          (BLUE, False, "Raw → Gold data flow (offline)"),
          (ORANGE, False, "Training / scoring / release flow (offline)"),
          (VIOLET, False, "Evidence / audit / governance flow"),
          (INK, True, "Scheduled job / asynchronous flow")]
for i, (color, dashed, label) in enumerate(legend):
    y = 1026 + i * 15
    _add(f"lg{i}a", "point;", 1720, y, 1, 1, parent="legend")
    _add(f"lg{i}b", "point;", 1800, y, 1, 1, parent="legend")
    edge(f"lg{i}", f"lg{i}a", f"lg{i}b", color=color, dashed=dashed)
    note(f"lg{i}t", 1810, y - 7, 168, 14, label, "legend", size=9, align="left")

# ====================================================================== edges
E = edge
E("e-spec", "spec", "ng", color=GREEN, pts=[(140, 262), (140, 345)], exit=(1, .5), entry=(0, .5))
E("e-mgr", "mgr", "ng", color=GREEN, pts=[(140, 390), (140, 345)], exit=(1, .5), entry=(0, .5))
E("e-ls", "ng", "ls", dashed=True, both=True, exit=(.5, 0), entry=(.26, 1))
E("e-ng", "ng", "nginx", "Bearer JWT<br>+ REST/JSON", color=GREEN)
E("e-nginx", "nginx", "fapi", color=GREEN)
E("e-api", "fapi", "app", color=GREEN, pts=[(680, 345), (680, 281)])
E("e-ad", "app", "dom", exit=(1, .45), entry=(0, .45))
E("e-di", "dom", "inf", exit=(1, .45), entry=(0, .45))
E("e-proj", "appschema", "dom", "", color=VIOLET, exit=(.85, 0), entry=(.35, 1),
  pts=[(970, 520)])
E("e-rw", "dom", "appschema", "", both=True, exit=(.6, 1), entry=(.95, 0))
E("e-files", "web", "evid", "POST /files<br>(evidence upload)", color=VIOLET, exit=(.2, 1),
  entry=(.32, 0))
E("e-meta", "evid", "ae", color=VIOLET, dashed=True, exit=(1, .85), entry=(.5, 1),
  pts=[(586, 1068)])
E("e-audit", "audit", "appschema", "Append audit events<br>(in same transaction)",
  color=VIOLET, dashed=True, exit=(.2, 0), entry=(.25, 1), pts=[(543, 842), (780, 842)])
E("p1", "csv", "manifest", "Load raw data", color=BLUE, exit=(1, .5), entry=(0, .5))
E("p2", "manifest", "bronze-pg", "Store snapshot", color=BLUE)
E("p3", "bronze-pg", "dbt", color=BLUE)
for i in range(3):
    E(f"pd{i}", f"L{i}", f"L{i + 1}", color=INK)
E("p4", "L3", "gold", "Build modelling dataset", color=INK, exit=(.5, 1), entry=(.5, 0),
  pts=[(1918, 318), (1538, 318)])
E("p5", "gold", "parq", color=BLUE)
E("p6", "parq", "train", color=ORANGE, exit=(.5, 1), entry=(.84, 0))
E("tr1", "t-temporal", "t-cal", color=INK)
E("tr2", "t-cal", "t-art", color=INK)
E("tr3", "t-art", "score", color=ORANGE, exit=(.5, 1), entry=(.94, 0))
E("s1", "s-rel", "s-max", color=INK)
E("s2", "s-max", "s-write", color=INK)
E("s3", "s-write", "s-queue", color=ORANGE)
E("e-ml", "s-write", "mlschema", "Write item predictions +<br>order risk (insert-only)",
  color=ORANGE, exit=(.5, 1), entry=(1, .9), pts=[(1747, 788), (1280, 788)])
E("e-seed", "s-queue", "appschema", "Seed review_cases (queue seeding)", color=VIOLET,
  exit=(.5, 1), entry=(.6, 1), pts=[(1903, 800), (891, 800)])
E("sm1", "st-p", "st-i", "claim / assign", color=INK, exit=(0, .5), entry=(.5, 0),
  pts=[(1143, 891)])
E("sm2", "st-i", "st-c", "complete", color=INK)
E("sm3", "st-i", "st-s", "skip", color=INK, exit=(.5, 1), entry=(0, .5), pts=[(1143, 1027)])
E("sm4", "st-c", "st-p", "Manager reopen", dashed=True, exit=(.5, 0), entry=(1, .3),
  pts=[(1360, 882)])
E("sm5", "st-s", "st-p", "", dashed=True, exit=(1, .5), entry=(1, .8),
  pts=[(1446, 1027), (1446, 905)])
for i in range(3):
    E(f"rte{i}", f"rt{i}", f"rt{i + 1}", color=INK)


# ====================================================================== writers
def _ids_attr(c, parent_abs):
    px, py = parent_abs
    return (f'<mxGeometry x="{c["x"] - px:g}" y="{c["y"] - py:g}" width="{c["w"]:g}" '
            f'height="{c["h"]:g}" as="geometry"/>')


def write_drawio(path: Path) -> None:
    out = ['<mxfile host="generator"><diagram id="arch" name="System Architecture">',
           '<mxGraphModel dx="2000" dy="1130" grid="0" gridSize="10" guides="1" tooltips="1" '
           'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2000" '
           'pageHeight="1130" math="0" shadow="0" adaptiveColors="auto"><root>',
           '<mxCell id="0"/><mxCell id="1" parent="0"/>']
    for c in cells:
        val = quoteattr(c["value"])
        if c["kind"] == "edge":
            pts = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in c["pts"])
            pts = f'<Array as="points">{pts}</Array>' if pts else ""
            out.append(f'<mxCell id="{c["id"]}" value={val} style={quoteattr(c["style"])} '
                       f'edge="1" parent="1" source="{c["src"]}" target="{c["tgt"]}">'
                       f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')
        else:
            parent = c["parent"] or "1"
            pabs = absolute[c["parent"]][:2] if c["parent"] else (0, 0)
            out.append(f'<mxCell id="{c["id"]}" value={val} style={quoteattr(c["style"])} '
                       f'vertex="1" parent="{parent}">{_ids_attr(c, pabs)}</mxCell>')
    out.append("</root></mxGraphModel></diagram></mxfile>")
    path.write_text("\n".join(out), encoding="utf-8")


def _style(c, key, default=None):
    m = re.search(rf"(?:^|;){key}=([^;]*)", c["style"])
    return m.group(1) if m else default


def write_preview(path: Path) -> None:
    """ponytail: rough SVG preview for checking layout without draw.io Desktop."""
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="1130">',
           '<rect width="2000" height="1130" fill="#fff"/>',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
           'markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" '
           'fill="context-stroke"/></marker></defs>']

    def text_block(x, y, w, h, value, size, color, align, valign):
        lines = [re.sub(r"<[^>]+>", "", s).replace("&amp;", "&").replace("&nbsp;", " ")
                 for s in re.split(r"<br>", value)]
        lh = size * 1.25
        top = y + 4 if valign == "top" else y + (h - lh * len(lines)) / 2
        anchor = {"left": "start", "center": "middle"}[align]
        tx = x + 6 if align == "left" else x + w / 2
        for i, line in enumerate(lines):
            svg.append(f'<text x="{tx}" y="{top + lh * (i + .8)}" font-size="{size}" '
                       f'font-family="Comic Sans MS" fill="{color}" text-anchor="{anchor}">'
                       f'{escape(line)}</text>')

    for c in cells:
        if c["kind"] == "edge" or c["style"] == "point;":
            continue
        x, y, w, h = c["x"], c["y"], c["w"], c["h"]
        size = float(_style(c, "fontSize", 11))
        if "shape=image" in c["style"]:
            svg.append(f'<image href="{_style(c, "image")}" x="{x}" y="{y}" width="{w}" '
                       f'height="{h}"/>'.replace("svg+xml,", "svg+xml;base64,"))
            if c["value"]:
                text_block(x - 50, y + h + 2, w + 100, 40, c["value"], size, INK, "center", "top")
            continue
        if not c["style"].startswith("text;"):
            fill = _style(c, "fillColor")
            dash = ' stroke-dasharray="8 5"' if "dashed=1" in c["style"] else ""
            svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
                       f'fill="{"none" if fill == "none" else fill}" '
                       f'stroke="{_style(c, "strokeColor")}" stroke-width="2"{dash}/>')
        if c["value"]:
            pad = float(_style(c, "spacingLeft", 0))
            text_block(x + pad, y, w - pad, h, c["value"], size,
                       _style(c, "fontColor", INK), _style(c, "align", "center"),
                       _style(c, "verticalAlign", "middle"))
    for c in cells:
        if c["kind"] != "edge":
            continue
        sx, sy, sw, sh = absolute[c["src"]]
        tx, ty, tw, th = absolute[c["tgt"]]
        a = (sx + sw * c["exit"][0], sy + sh * c["exit"][1])
        b = (tx + tw * c["entry"][0], ty + th * c["entry"][1])
        pts, prev = [a], a
        for p in c["pts"] + [b]:
            if prev[0] != p[0] and prev[1] != p[1]:
                pts.append((p[0], prev[1]) if c["exit"][1] in (0.5, .45) and len(pts) == 1
                           else (prev[0], p[1]))
            pts.append(p)
            prev = p
        color = _style(c, "strokeColor")
        dash = ' stroke-dasharray="7 5"' if "dashed=1" in c["style"] else ""
        start = ' marker-start="url(#a)"' if "startArrow" in c["style"] else ""
        poly = " ".join(f"{x},{y}" for x, y in pts)
        svg.append(f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2"'
                   f'{dash} marker-end="url(#a)"{start}/>')
        if c["value"]:
            mx = (pts[len(pts) // 2 - 1][0] + pts[len(pts) // 2][0]) / 2
            my = (pts[len(pts) // 2 - 1][1] + pts[len(pts) // 2][1]) / 2
            text_block(mx - 90, my - 14, 180, 28, c["value"], 10, color, "center", "middle")
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


if __name__ == "__main__":
    write_drawio(OUT)
    ids = [c["id"] for c in cells]
    assert len(ids) == len(set(ids)), "duplicate cell ids"
    assert all(c["src"] in absolute and c["tgt"] in absolute
               for c in cells if c["kind"] == "edge"), "edge to unknown cell"
    if "--preview" in sys.argv:
        write_preview(Path(sys.argv[sys.argv.index("--preview") + 1]))
    print(f"Wrote {OUT} ({len(cells)} cells)")

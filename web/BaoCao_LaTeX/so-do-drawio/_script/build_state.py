"""Vòng đời case: nhãn đặt cạnh đường nối, không đè lên mũi tên."""
from pathlib import Path
from dio import D
OUT = Path(__file__).parent / "drawio"
F = "fontFamily=Helvetica;html=1;whiteSpace=wrap;"
ST = F + "rounded=1;arcSize=40;fillColor=#ffffff;strokeColor=#222222;fontSize=14;"
L = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;endSize=7;strokeColor=#222222;"
     "fontFamily=Helvetica;fontSize=13;labelBackgroundColor=none;")
sub = lambda t: f"<span style='font-weight:normal;font-size:12px'>{t}</span>"
d = D("vong-doi-case")
s0 = d.node("", 0, 100, 24, 24, F + "ellipse;fillColor=#111111;strokeColor=#111111;")
p = d.node(f"<b>PENDING</b><br>{sub('chờ nhận / chờ giao')}", 170, 80, 180, 64, ST)
ip = d.node(f"<b>IN_PROGRESS</b><br>{sub('đang có người giữ')}", 560, 80, 180, 64, ST)
co = d.node(f"<b>COMPLETED</b><br>{sub('HAS_ISSUE / NO_ISSUE / DUPLICATE')}", 960, -40, 250, 64, ST)
sk = d.node(f"<b>SKIPPED</b><br>{sub('UNREACHABLE / REFUSED / ...')}", 960, 200, 250, 64, ST)
d.edge(s0, p, "seed từ dự đoán", L, extra="exitX=1;exitY=0.5;entryX=0;entryY=0.5;verticalAlign=bottom;", off=(0, -8))
d.edge(p, ip, "claim (NV) / assign (QL)", L, extra="exitX=1;exitY=0.5;entryX=0;entryY=0.5;verticalAlign=bottom;", off=(0, -8))
d.edge(ip, co, "complete", L, extra="exitX=1;exitY=0.3;entryX=0;entryY=0.5;", pts=[(850, 99), (850, -8)], pos=0, off=(50, 0))
d.edge(ip, sk, "skip / tự đóng khi hết lượt", L, extra="exitX=1;exitY=0.7;entryX=0;entryY=0.5;", pts=[(850, 125), (850, 232)], pos=0, off=(100, 0))
d.edge(ip, ip, "reassign, ghi liên lạc", L, extra="exitX=0.3;exitY=1;entryX=0.7;entryY=1;verticalAlign=top;", pts=[(614, 200), (686, 200)], off=(0, 6))
d.edge(co, p, "reopen (QL) → chu kỳ mới", L, extra="exitX=0.5;exitY=0;entryX=0.5;entryY=0;verticalAlign=bottom;", pts=[(1085, -90), (260, -90)], off=(0, -6))
d.edge(sk, p, "reopen (QL) → chu kỳ mới", L, extra="exitX=0.5;exitY=1;entryX=0.5;entryY=1;verticalAlign=top;", pts=[(1085, 320), (260, 320)], off=(0, 6))
(OUT / "vong-doi-case.drawio").write_text(d.xml())
print("state ok")

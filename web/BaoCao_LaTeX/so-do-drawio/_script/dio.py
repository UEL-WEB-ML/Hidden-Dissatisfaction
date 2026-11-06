"""Bộ dựng sơ đồ draw.io (mxGraph XML) cho báo cáo môn Web."""
from xml.sax.saxutils import escape

FONT = "fontFamily=Helvetica;fontSize=12;"
S = {
    # chung
    "box": "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#333333;" + FONT,
    "rbox": "rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor=#dae8fc;strokeColor=#6c8ebf;" + FONT,
    "note": "shape=note;whiteSpace=wrap;html=1;size=12;fillColor=#fff2cc;strokeColor=#d6b656;align=left;spacingLeft=6;" + FONT + "fontSize=11;",
    "text": "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;" + FONT,
    # BPMN
    "pool": "swimlane;horizontal=0;startSize=28;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;" + FONT,
    "lane": "swimlane;horizontal=0;startSize=28;html=1;fillColor=#ffffff;strokeColor=#999999;swimlaneFillColor=#ffffff;" + FONT,
    "task": "rounded=1;whiteSpace=wrap;html=1;arcSize=14;fillColor=#dae8fc;strokeColor=#6c8ebf;" + FONT + "fontSize=11;",
    "systask": "rounded=1;whiteSpace=wrap;html=1;arcSize=14;fillColor=#e1d5e7;strokeColor=#9673a6;" + FONT + "fontSize=11;",
    "start": "ellipse;html=1;fillColor=#d5e8d4;strokeColor=#82b366;strokeWidth=1.5;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;" + FONT + "fontSize=10;",
    "end": "ellipse;html=1;fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=3.5;labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;" + FONT + "fontSize=10;",
    "gw": "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" + FONT + "fontSize=10;",
    "datastore": "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=8;fillColor=#f5f5f5;strokeColor=#666666;" + FONT + "fontSize=10;",
    # DFD (Gane–Sarson)
    "ext": "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontStyle=1;shadow=1;strokeWidth=1.5;" + FONT,
    "proc": "rounded=1;whiteSpace=wrap;html=1;arcSize=18;fillColor=#dae8fc;strokeColor=#6c8ebf;verticalAlign=middle;" + FONT,
    "store": "shape=partialRectangle;whiteSpace=wrap;html=1;right=0;fillColor=#f5f5f5;strokeColor=#666666;align=left;spacingLeft=8;" + FONT + "fontSize=11;",
    # FDD
    "fdd0": "rounded=0;whiteSpace=wrap;html=1;fillColor=#1f4e79;fontColor=#ffffff;strokeColor=#1f4e79;fontStyle=1;" + FONT + "fontSize=13;",
    "fdd1": "rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;" + FONT,
    "fdd2": "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#6c8ebf;align=left;spacingLeft=6;" + FONT + "fontSize=11;",
    # Use case
    "actor": "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#ffffff;strokeColor=#333333;" + FONT + "fontStyle=1;",
    "uc": "ellipse;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" + FONT + "fontSize=11;",
    "ucm": "ellipse;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;" + FONT + "fontSize=11;",
    "boundary": "rounded=0;whiteSpace=wrap;html=1;fillColor=#f4f4f4;strokeColor=#333333;verticalAlign=top;fontStyle=1;" + FONT + "fontSize=13;",
    # trạng thái
    "state": "rounded=1;whiteSpace=wrap;html=1;arcSize=40;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;" + FONT,
    # ERD
    "tbl": "swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;swimlaneFillColor=#ffffff;" + FONT,
    "tblml": "swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;html=1;fillColor=#d5e8d4;strokeColor=#82b366;swimlaneFillColor=#ffffff;" + FONT,
    "row": "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=18;spacingRight=14;overflow=hidden;html=1;" + FONT + "fontSize=10.5;",
    "group": "rounded=1;whiteSpace=wrap;html=1;arcSize=4;fillColor=none;dashed=1;strokeColor=#999999;verticalAlign=top;align=left;spacingLeft=8;fontStyle=1;" + FONT + "fontColor=#666666;",
}
E = {
    "flow": "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor=#333333;" + FONT + "fontSize=10;labelBackgroundColor=#ffffff;",
    "line": "edgeStyle=none;html=1;endArrow=none;strokeColor=#333333;",
    "arrow": "edgeStyle=none;html=1;endArrow=block;endFill=1;strokeColor=#333333;" + FONT + "fontSize=10;labelBackgroundColor=#ffffff;",
    "data": "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;endFill=1;strokeColor=#555555;" + FONT + "fontSize=10;labelBackgroundColor=#ffffff;",
    "dashed": "edgeStyle=none;html=1;endArrow=open;dashed=1;strokeColor=#555555;" + FONT + "fontSize=10;labelBackgroundColor=#ffffff;",
    "tree": "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=none;strokeColor=#6c8ebf;rounded=0;",
    "er": "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=ERmany;startArrow=ERmandOne;endFill=0;startFill=0;strokeColor=#555555;rounded=1;",
    "er01": "edgeStyle=orthogonalEdgeStyle;html=1;endArrow=ERmany;startArrow=ERzeroToOne;endFill=0;startFill=0;strokeColor=#555555;rounded=1;",
    "inherit": "edgeStyle=none;html=1;endArrow=block;endFill=0;endSize=12;strokeColor=#333333;",
}


import re as _re


def mono(st):
    """Kiểu báo cáo mẫu: nền trắng, nét đen."""
    if "childLayout=stackLayout" in st:
        st = _re.sub(r"fillColor=#[0-9a-fA-F]{6}", "fillColor=#e9e9e9", st)
    else:
        st = _re.sub(r"fillColor=#(?!f4f4f4|111111)[0-9a-fA-F]{6}", "fillColor=#ffffff", st)
    st = _re.sub(r"strokeColor=#(?!111111)[0-9a-fA-F]{6}", "strokeColor=#222222", st)
    st = st.replace("fontColor=#ffffff", "fontColor=#111111").replace("fontColor=#666666", "fontColor=#444444")
    st = st.replace("swimlaneFillColor=#ffffff", "swimlaneFillColor=#ffffff")
    return st


class D:
    def __init__(self, name):
        self.name, self.cells, self.n, self.geo = name, [], 0, {}

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def node(self, label, x, y, w, h, style="box", id=None, parent="1", extra=""):
        id = id or self._id()
        st = mono(S.get(style, style) + extra)
        self.geo[id] = (x, y, w, h)
        self.cells.append(f'<mxCell id="{id}" value="{escape(label, {chr(34): "&quot;"})}" style="{st}" vertex="1" parent="{parent}">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return id

    def edge(self, s, t, label="", style="flow", pts=None, extra="", off=None, src=None, dst=None, pos=None):
        id = self._id()
        st = mono(E.get(style, style) + extra)
        g = '<mxGeometry relative="1" as="geometry">' if pos is None else f'<mxGeometry x="{pos}" relative="1" as="geometry">'
        if src:
            g += f'<mxPoint x="{src[0]}" y="{src[1]}" as="sourcePoint"/>'
        if dst:
            g += f'<mxPoint x="{dst[0]}" y="{dst[1]}" as="targetPoint"/>'
        if off:
            g += f'<mxPoint x="{off[0]}" y="{off[1]}" as="offset"/>'
        if pts:
            g += '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in pts) + "</Array>"
        g += "</mxGeometry>"
        self.cells.append(f'<mxCell id="{id}" value="{escape(label, {chr(34): "&quot;"})}" style="{st}" edge="1" parent="1" source="{s}" target="{t}">{g}</mxCell>')
        return id

    def table(self, title, rows, x, y, w=210, style="tbl"):
        h = 26 + 20 * len(rows)
        tid = self.node(title, x, y, w, h, style)
        for i, r in enumerate(rows):
            self.node(r, 0, 26 + 20 * i, w, 20, "row", parent=tid)
        return tid

    def xml(self):
        body = "".join(self.cells)
        return (f'<mxfile host="drawio"><diagram name="{escape(self.name)}" id="{self.name}"><mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" '
                f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram></mxfile>')


class BPMN(D):
    """BPMN dọc: lane là cột, bước (col) chạy từ trên xuống."""

    def __init__(self, name, pool, lanes, cols, colw=92, laneh=235, x0=20, y0=20):
        super().__init__(name)
        self.colw, self.laneh, self.x0, self.y0, self.lanes = colw, laneh, x0, y0, lanes
        H = 56 + cols * colw
        self.poolidx = len(self.cells)
        self.node(pool, x0, y0, laneh * len(lanes), H + 10, S["pool"].replace("horizontal=0;", ""))
        for i, ln in enumerate(lanes):
            self.node(ln, x0 + i * laneh, y0 + 28, laneh, H - 18, S["lane"].replace("horizontal=0;", ""))

    def xml(self):
        bottom = max(y + h for k, (x, y, w, h) in self.geo.items() if k not in ("c1",) and not k.startswith("c1_")) 
        lanes = [k for k in list(self.geo)[1:1 + len(self.lanes)]]
        need = bottom + 30 - self.y0
        import re
        for i in range(self.poolidx, self.poolidx + 1 + len(self.lanes)):
            hh = need if i == self.poolidx else need - 28
            self.cells[i] = re.sub(r'height="[0-9.]+"', f'height="{hh}"', self.cells[i])
        return super().xml()

    def c(self, lane, col):
        return (self.x0 + lane * self.laneh + self.laneh / 2, self.y0 + 56 + 10 + col * self.colw + self.colw / 2)

    def side(self, col, lane=0):
        return (self.x0 + lane * self.laneh + 14, self.c(lane, col)[1])

    def at(self, kind, label, lane, col, w=None, h=None, dy=0, dx=0):
        cx, cy = self.c(lane, col)
        size = {"start": (34, 34), "end": (34, 34), "gw": (120, 64), "task": (160, 56), "systask": (160, 56), "datastore": (90, 56)}[kind]
        w, h = w or size[0], h or size[1]
        st = kind
        if kind in ("start", "end"):
            st = S[kind].replace("labelPosition=center;verticalLabelPosition=bottom;align=center;verticalAlign=top;",
                                 "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=4;")
        return self.node(label, cx - w / 2 + dx, cy - h / 2 + dy, w, h, st)

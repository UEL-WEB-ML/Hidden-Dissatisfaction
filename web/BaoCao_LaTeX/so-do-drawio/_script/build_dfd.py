"""DFD kiểu báo cáo mẫu: trắng đen, đường vuông góc, thực thể có bóng, kho có ô mã."""
from pathlib import Path
from dio import D

OUT = Path(__file__).parent / "drawio"
F = "fontFamily=Helvetica;html=1;whiteSpace=wrap;"
EXT = F + "rounded=0;fillColor=#ffffff;strokeColor=#222222;strokeWidth=1.5;shadow=1;fontStyle=1;fontSize=14;"
PROC = F + "rounded=1;arcSize=12;fillColor=#ffffff;strokeColor=#222222;fontSize=13;"
STORE = F + "shape=partialRectangle;right=0;fillColor=#ffffff;strokeColor=#222222;align=left;spacingLeft=44;fontSize=13;"
IDBOX = F + "rounded=0;fillColor=none;strokeColor=#222222;fontStyle=1;fontSize=13;"
AR = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;endSize=7;strokeColor=#222222;"
      "fontFamily=Helvetica;fontSize=12;labelBackgroundColor=#ffffff;")


CUBE = F + ("shape=cube;size=10;boundedLbl=1;backgroundOutline=1;darkOpacity=0.55;darkOpacity2=0.25;"
            "fillColor=#ffffff;strokeColor=#222222;fontStyle=1;fontSize=14;spacingLeft=16;spacingTop=14;")
NUM = F + "rounded=0;fillColor=#ffffff;strokeColor=#222222;fontSize=11;"
LANE = F + ("swimlane;rounded=1;arcSize=8;startSize=24;horizontal=1;fillColor=#ffffff;swimlaneFillColor=#ffffff;"
            "strokeColor=#222222;fontStyle=0;fontSize=12;collapsible=0;")
BODY = F + "text;align=center;verticalAlign=middle;fontSize=13;strokeColor=none;fillColor=none;"
ENO = {"Nhân viên CSKH": "1", "Quản lý": "2"}


class DFD(D):
    def ext(self, t, x, y, w=140, h=64, n=None):
        n = n or ENO.get(t.split("<")[0], "3")
        eid = self.node(t, x, y, w, h, CUBE)
        self.node(n, 10, 10, 20, 18, NUM, parent=eid)
        return eid

    def proc(self, n, t, x, y, w=170, h=80):
        pid = self.node(n, x, y, w, h, LANE)
        self.node(t, 0, 24, w, h - 24, BODY, parent=pid)
        return pid

    def store(self, n, t, x, y, w=210, h=34):
        sid = self.node(t, x, y, w, h, STORE)
        self.node(n, 0, 0, 36, h, IDBOX, parent=sid)
        return sid

    def f(self, s, t, label="", ex=0.5, ey=0.5, nx=0.5, ny=0.5, pts=None, pos=None):
        return self.edge(s, t, label, AR, pts=pts, extra=f"exitX={ex};exitY={ey};entryX={nx};entryY={ny};", pos=pos)


def save(d, name):
    (OUT / f"{name}.drawio").write_text(d.xml())


# =============================== DFD mức 0 ===============================
d = DFD("dfd-muc-0")
nv = d.ext("Nhân viên<br>CSKH", 0, 300, 140, 70, n="1")
ql = d.ext("Quản lý", 1080, 400, 140, 70)
ml = d.ext("Quy trình chấm<br>điểm ML", 1080, 0, 140, 64, n="3")
p7 = d.proc("7", "Nạp dự đoán<br>và tạo case", 800, 0)
p2 = d.proc("2", "Quản lý hàng đợi<br>rủi ro", 230, 140)
p5 = d.proc("5", "Giám sát và<br>truy vết", 800, 260)
p3 = d.proc("3", "Xử lý case", 230, 520)
p4 = d.proc("4", "Ra quyết định", 800, 450)
p6 = d.proc("6", "Cấu hình vận hành", 800, 700)
p1 = d.proc("1", "Quản lý tài khoản", 530, 880)
D2 = d.store("D2", "Kết quả dự đoán", 500, 24)
D3 = d.store("D3", "Case, chu kỳ, phân công", 500, 270, 220)
D4 = d.store("D4", "Liên lạc, minh chứng", 500, 470, 220)
D5 = d.store("D5", "Nhận xét, quyết định", 500, 560, 220)
D6 = d.store("D6", "Nhật ký audit", 500, 650, 220)
D7 = d.store("D7", "Tham số", 500, 740, 220)
D1 = d.store("D1", "Người dùng", 520, 1010, 190)
d.f(ml, p7, "dự đoán", 0, 0.5, 1, 0.375)
d.f(p7, D2, "lưu điểm", 0, 0.5, 1, 0.47)
d.f(D2, p2, "điểm, yếu tố", 0, 0.47, 0.5, 0, pts=[(315, 40)])
d.f(p7, D3, "case mới", 0.12, 1, 0.68, 0, pts=[(820, 230), (650, 230)])
d.f(p2, D3, "phân công", 1, 0.75, 0, 0.5, pts=[(450, 200), (450, 287)])
d.f(nv, p2, "lọc, nhận đơn", 0.5, 0, 0, 0.5, pts=[(70, 180)])
d.f(p2, nv, "hàng đợi, chi tiết", 0.25, 1, 1, 0.2857, pts=[(272, 320)])
d.f(ql, p2, "giao / chuyển đơn", 0.3, 0, 1, 0.25, pts=[(1122, 110), (430, 110), (430, 160)])
d.f(D3, p5, "case, SLA", 1, 0.75, 0, 0.45)
d.f(p5, ql, "tổng quan, lịch sử", 1, 0.75, 0, 0.2857, pts=[(1040, 320), (1040, 420)])
d.f(D6, p5, "nhật ký", 1, 0.5, 0, 0.875, pts=[(775, 667), (775, 330)], pos=0.75)
d.f(nv, p3, "liên lạc, đóng case", 0.3, 1, 0, 0.5, pts=[(42, 560)])
d.f(p3, D3, "trạng thái", 0.75, 0, 0.27, 1, pts=[(357, 400), (560, 400)])
d.f(p3, D4, "lần liên lạc", 1, 0.15, 0, 0.5, pts=[(450, 532), (450, 487)])
d.f(p3, D5, "nhận xét", 1, 0.7, 0, 0.47)
d.f(p3, D6, "audit", 0.75, 1, 0, 0.5, pts=[(357, 667)])
d.f(D7, p3, "max_contact", 0, 0.5, 0.25, 1, pts=[(272, 757)])
d.f(ql, p3, "mở lại", 1, 0.5, 0.5, 1, pts=[(1250, 435), (1250, 830), (315, 830)])
d.f(ql, p4, "quyết định", 0.3, 1, 1, 0.625, pts=[(1122, 500)])
d.f(D4, p4, "liên lạc", 1, 0.5, 0, 0.45)
d.f(p4, D5, "quyết định", 0, 0.85, 1, 0.47, pts=[(745, 518), (745, 577)], pos=-0.75)
d.f(p4, D6, "audit", 0.3, 1, 1, 0.3, pts=[(851, 660)], pos=-0.4)
d.f(ql, p6, "tham số mới", 0.7, 1, 1, 0.5, pts=[(1178, 740)])
d.f(p6, D7, "phiên bản", 0, 0.7, 1, 0.5)
d.f(nv, p1, "đăng nhập", 0.7, 1, 0, 0.5, pts=[(98, 920)])
d.f(ql, p1, "đăng nhập", 0.9, 1, 1, 0.25, pts=[(1206, 900)])
d.f(p1, D1, "tài khoản", 0.5, 1, 0.5, 0)
save(d, "dfd-muc-0")

# =============================== DFD-1: hàng đợi ===============================
d = DFD("dfd-1-hang-doi")
nv = d.ext("Nhân viên CSKH", 0, 200, 130, 64)
ql = d.ext("Quản lý", 900, 200, 130, 64)
a1 = d.proc("2.1", "Lọc và sắp xếp<br>hàng đợi", 220, 40, 150, 70)
a2 = d.proc("2.2", "Xem chi tiết đơn", 220, 200, 150, 70)
a3 = d.proc("2.3", "Nhận đơn", 220, 360, 150, 70)
a4 = d.proc("2.4", "Giao / chuyển đơn", 690, 360, 150, 70)
D2 = d.store("D2", "Kết quả dự đoán", 470, 40, 200)
D3 = d.store("D3", "Case, chu kỳ, phân công", 470, 204, 200)
D7 = d.store("D7", "Tham số (capacity)", 470, 380, 200)
D6 = d.store("D6", "Nhật ký audit", 470, 480, 200)
D1 = d.store("D1", "Người dùng", 680, 220, 180)
d.f(nv, a1, "bộ lọc", 0.3, 0, 0, 0.5, pts=[(39, 75)])
d.f(a1, nv, "trang kết quả", 0, 0.85, 0.8, 0, pts=[(104, 100)])
d.f(D2, a1, "điểm, mức", 0, 0.47, 1, 0.23)
d.f(D3, a1, "trạng thái, SLA", 0, 0.2, 1, 0.78, pts=[(420, 211), (420, 95)])
d.f(nv, a2, "mã đơn", 1, 0.5, 0, 0.5)
d.f(D3, a2, "chu kỳ, liên lạc", 0, 0.75, 1, 0.5)
d.f(nv, a3, "lệnh Nhận", 0.5, 1, 0, 0.5, pts=[(65, 395)])
d.f(D7, a3, "capacity", 0, 0.47, 1, 0.5)
d.f(a3, D3, "IN_PROGRESS, phân công", 0.8, 0, 0.25, 1, pts=[(340, 320), (520, 320)])
d.f(a3, D6, "audit CLAIM", 0.5, 1, 0, 0.5, pts=[(295, 497)])
d.f(ql, a4, "nhân viên, lý do", 0.5, 1, 1, 0.5, pts=[(965, 395)])
d.f(D1, a4, "tải việc", 0.5, 1, 0.5, 0)
d.f(a4, D3, "phân công mới", 0, 0.2, 0.65, 1, pts=[(600, 374)])
d.f(a4, D6, "audit ASSIGN", 0.5, 1, 1, 0.5, pts=[(765, 497)])
save(d, "dfd-1-hang-doi")

# =============================== DFD-1: xử lý case ===============================
d = DFD("dfd-1-xu-ly-case")
nv = d.ext("Nhân viên CSKH", 0, 260, 130, 64)
ql = d.ext("Quản lý", 990, 333, 130, 64)
b2 = d.proc("3.2", "Tải minh chứng", 220, 0, 150, 70)
b1 = d.proc("3.1", "Ghi nhận liên lạc", 220, 120, 150, 70)
b3 = d.proc("3.3", "Hoàn tất / bỏ qua", 220, 300, 150, 70)
b6 = d.proc("3.6", "Thêm nhận xét", 220, 460, 150, 70)
b4 = d.proc("3.4", "Tự đóng<br>UNREACHABLE", 720, 120, 150, 70)
b5 = d.proc("3.5", "Mở lại case", 720, 330, 150, 70)
D4 = d.store("D4", "Liên lạc, minh chứng", 470, 40, 200)
D7 = d.store("D7", "Tham số", 730, 20, 150)
D3 = d.store("D3", "Case, chu kỳ, phân công", 470, 300, 200)
D6 = d.store("D6", "Nhật ký audit", 470, 400, 200)
D5 = d.store("D5", "Nhận xét, quyết định", 470, 500, 200)
d.f(nv, b2, "tệp PNG/JPG/PDF", 0.3, 0, 0, 0.5, pts=[(39, 35)])
d.f(b2, D4, "tệp đã kiểm", 1, 0.8, 0, 0.47)
d.f(nv, b1, "kênh, kết quả", 0.7, 0, 0, 0.5, pts=[(91, 155)])
d.f(b1, D4, "lần liên lạc", 1, 0.2, 0.25, 1, pts=[(520, 134)])
d.f(b1, b4, "không liên lạc được", 1, 0.6, 0, 0.6)
d.f(D7, b4, "max_contact", 0.5, 1, 0.5, 0)
d.f(b4, D3, "SKIPPED", 0.5, 1, 1, 0.47, pts=[(795, 316)])
d.f(nv, b3, "kết quả / lý do", 0.5, 1, 0, 0.5, pts=[(65, 335)])
d.f(b3, D3, "đóng case", 1, 0.23, 0, 0.47)
d.f(b3, D6, "audit", 1, 0.7, 0, 0.5, pts=[(440, 349), (440, 417)])
d.f(ql, b5, "lý do, xác nhận", 0, 0.5, 1, 0.5)
d.f(b5, D3, "chu kỳ mới", 0, 0.2, 0.75, 1, pts=[(620, 344)])
d.f(b5, D6, "audit", 0, 0.7, 1, 0.5, pts=[(695, 379), (695, 417)])
d.f(nv, b6, "nội dung", 0.2, 1, 0, 0.5, pts=[(26, 495)])
d.f(b6, D5, "nhận xét", 1, 0.8, 0, 0.47)
save(d, "dfd-1-xu-ly-case")

# =============================== DFD-1: quyết định ===============================
d = DFD("dfd-1-quyet-dinh")
ql = d.ext("Quản lý", 0, 160, 130, 64)
c1 = d.proc("4.1", "Lấy case chờ<br>quyết định", 220, 0, 160, 76)
c2 = d.proc("4.2", "Ghi quyết định", 220, 155, 160, 76)
c3 = d.proc("4.3", "Ghi chú cho mô hình", 220, 320, 160, 76)
D3 = d.store("D3", "Case, chu kỳ, phân công", 560, 6, 210)
D4 = d.store("D4", "Liên lạc, minh chứng", 560, 50, 210)
D5 = d.store("D5", "Nhận xét, quyết định", 560, 160, 210)
D6 = d.store("D6", "Nhật ký audit", 560, 340, 210)
d.f(ql, c1, "mở trang", 0.3, 0, 0, 0.3, pts=[(39, 23)])
d.f(c1, ql, "danh sách, chi tiết", 0, 0.75, 0.75, 0, pts=[(97, 57)])
d.f(D3, c1, "case đã đóng", 0, 0.5, 1, 0.3)
d.f(D4, c1, "lịch sử liên lạc", 0, 0.5, 1, 0.88)
d.f(ql, c2, "quyết định, hạn", 1, 0.5, 0, 0.5)
d.f(c2, D5, "quyết định mới", 1, 0.3, 0, 0.5)
d.f(c2, D6, "audit DECISION", 1, 0.85, 0.4, 0, pts=[(644, 220)])
d.f(ql, c3, "ghi chú", 0.5, 1, 0, 0.5, pts=[(65, 358)])
d.f(c3, D6, "audit MODEL_NOTE", 1, 0.5, 0, 0.5)
save(d, "dfd-1-quyet-dinh")

# =============================== Ngữ cảnh ===============================
d = DFD("dfd-ngu-canh")
PX, PY, PW, PH = 400, 170, 230, 200
EW, EH = 170, 90
cy = PY + PH / 2
sys_ = d.proc("0", "Hệ thống hỗ trợ xử lý<br>đơn hàng có nguy cơ<br>không hài lòng ẩn", PX, PY, PW, PH)
nv = d.ext("Nhân viên CSKH", 0, cy - EH / 2, EW, EH)
ql = d.ext("Quản lý", PX + PW + (PX - EW), cy - EH / 2, EW, EH)
ml = d.ext("Quy trình chấm điểm ML<br><span style='font-weight:normal;font-size:13px'>(chạy theo lô)</span>", PX + PW / 2 - 130, -150, 260, 80, n="3")
L = "edgeStyle=none;html=1;endArrow=block;endFill=1;endSize=7;strokeColor=#222222;fontFamily=Helvetica;fontSize=13;labelBackgroundColor=none;"
yin, yout = cy - 26, cy + 26
r = lambda y, top, h: round((y - top) / h, 4)
d.edge(nv, sys_, "Đăng nhập, bộ lọc, lệnh nhận đơn,<br>lần liên lạc, minh chứng,<br>hoàn tất / bỏ qua, nhận xét", L,
       extra=f"exitX=1;exitY={r(yin, cy-EH/2, EH)};entryX=0;entryY={r(yin, PY, PH)};verticalAlign=bottom;", off=(0, -6))
d.edge(sys_, nv, "Hàng đợi ưu tiên, chi tiết đơn,<br>yếu tố rủi ro, SLA, slot còn lại,<br>thông báo kết quả", L,
       extra=f"exitX=0;exitY={r(yout, PY, PH)};entryX=1;entryY={r(yout, cy-EH/2, EH)};verticalAlign=top;", off=(0, 6))
d.edge(ql, sys_, "Giao / chuyển đơn, mở lại,<br>quyết định, ghi chú mô hình,<br>tham số mới", L,
       extra=f"exitX=0;exitY={r(yin, cy-EH/2, EH)};entryX=1;entryY={r(yin, PY, PH)};verticalAlign=bottom;", off=(0, -6))
d.edge(sys_, ql, "Số liệu tổng quan, tải việc,<br>case chờ quyết định,<br>lịch sử thao tác", L,
       extra=f"exitX=1;exitY={r(yout, PY, PH)};entryX=0;entryY={r(yout, cy-EH/2, EH)};verticalAlign=top;", off=(0, 6))
d.edge(ml, sys_, "Điểm rủi ro theo sản phẩm và đơn,<br>yếu tố liên quan, ngưỡng,<br>phiên bản mô hình", L,
       extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;align=left;labelPosition=right;spacingLeft=10;")
save(d, "dfd-ngu-canh")
print("dfd ok")

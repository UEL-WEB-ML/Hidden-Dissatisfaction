from pathlib import Path
from dio import D

OUT = Path(__file__).parent / "drawio"; OUT.mkdir(exist_ok=True)


def save(d, name):
    (OUT / f"{name}.drawio").write_text(d.xml())


# ======================= FDD ================================================
d = D("fdd")
root = d.node("HỆ THỐNG HỖ TRỢ XỬ LÝ ĐƠN HÀNG CÓ NGUY CƠ KHÔNG HÀI LÒNG ẨN", 250, 0, 520, 50, "fdd0")
groups = [
    ("1. Quản lý tài khoản", ["1.1 Đăng nhập", "1.2 Đăng xuất", "1.3 Xem hồ sơ", "1.4 Đổi ngôn ngữ Việt/Anh"]),
    ("2. Quản lý hàng đợi rủi ro", ["2.1 Xem Risk Queue", "2.2 Tìm kiếm, lọc, sắp xếp", "2.3 Xem chi tiết đơn", "2.4 Nhận đơn", "2.5 Giao / chuyển đơn"]),
    ("3. Xử lý case", ["3.1 Ghi nhận liên lạc", "3.2 Tải minh chứng", "3.3 Hoàn tất case", "3.4 Bỏ qua case", "3.5 Mở lại case", "3.6 Thêm nhận xét"]),
    ("4. Ra quyết định", ["4.1 Xem case chờ quyết định", "4.2 Ghi quyết định", "4.3 Ghi chú cho mô hình"]),
    ("5. Giám sát và truy vết", ["5.1 Xem tổng quan rủi ro", "5.2 Xem theo đơn / sản phẩm", "5.3 Xem lịch sử thao tác"]),
    ("6. Cấu hình vận hành", ["6.1 Xem tham số hiện hành", "6.2 Tạo phiên bản tham số", "6.3 Hẹn giờ hiệu lực"]),
    ("7. Nạp kết quả dự đoán", ["7.1 Nhận snapshot điểm rủi ro", "7.2 Tạo case cho đơn mới"]),
]
W, G = 138, 10
for i, (g, kids) in enumerate(groups):
    x = i * (W + G)
    gid = d.node(g, x, 110, W, 46, "fdd1")
    d.edge(root, gid, "", "tree", extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    for j, k in enumerate(kids):
        kid = d.node(k, x + 14, 180 + j * 48, W - 14, 38, "fdd2")
        d.edge(gid, kid, "", "tree", extra="exitX=0.08;exitY=1;entryX=0;entryY=0.5;")
save(d, "fdd")

# ======================= Ngữ cảnh ===========================================
d = D("dfd-ngu-canh")
sys_ = d.node("<b>0</b><hr>Hệ thống hỗ trợ xử lý đơn hàng có nguy cơ không hài lòng ẩn", 330, 190, 220, 120, "proc")
nv = d.node("Nhân viên CSKH", 0, 220, 140, 60, "ext")
ql = d.node("Quản lý", 740, 220, 140, 60, "ext")
ml = d.node("Quy trình chấm điểm ML (chạy theo lô)", 350, 0, 180, 60, "ext")
d.edge(nv, sys_, "Thông tin đăng nhập; bộ lọc; lệnh nhận đơn;<br>lần liên lạc, minh chứng; hoàn tất / bỏ qua; nhận xét", "arrow", pts=[(70, 170), (440, 170)], extra="exitX=0.5;exitY=0;entryX=0.3;entryY=0;")
d.edge(sys_, nv, "Hàng đợi ưu tiên; chi tiết đơn và yếu tố rủi ro;<br>SLA, slot còn lại; thông báo kết quả", "arrow", pts=[(440, 350), (70, 350)], extra="exitX=0.3;exitY=1;entryX=0.5;entryY=1;")
d.edge(ql, sys_, "Lệnh giao / chuyển đơn; mở lại;<br>quyết định; ghi chú mô hình; tham số mới", "arrow", pts=[(810, 150), (500, 150)], extra="exitX=0.5;exitY=0;entryX=0.8;entryY=0;")
d.edge(sys_, ql, "Số liệu tổng quan; tải việc nhân viên;<br>case chờ quyết định; lịch sử thao tác", "arrow", pts=[(500, 390), (810, 390)], extra="exitX=0.8;exitY=1;entryX=0.5;entryY=1;")
d.edge(ml, sys_, "Điểm rủi ro theo sản phẩm và đơn,<br>yếu tố liên quan, ngưỡng, phiên bản mô hình", "arrow", extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
save(d, "dfd-ngu-canh")

# ======================= DFD mức 0 ==========================================
d = D("dfd-muc-0")
P = lambda n, t, x, y: d.node(f"<b>{n}</b><hr>{t}", x, y, 150, 74, "proc")
ST = lambda n, t, x, y, w=180: d.node(f"<b>{n}</b> &nbsp;|&nbsp; {t}", x, y, w, 32, "store")
nv = d.node("Nhân viên CSKH", 0, 300, 130, 56, "ext")
ql = d.node("Quản lý", 880, 300, 130, 56, "ext")
ml = d.node("Quy trình chấm điểm ML", 870, 40, 150, 56, "ext")
p1 = P("1", "Quản lý tài khoản", 400, 0)
p7 = P("7", "Nạp dự đoán và tạo case", 660, 30)
D1 = ST("D1", "Người dùng", 385, 110)
D2 = ST("D2", "Kết quả dự đoán", 645, 150)
p2 = P("2", "Quản lý hàng đợi rủi ro", 200, 190)
p5 = P("5", "Giám sát và truy vết", 660, 220)
D3 = ST("D3", "Case, chu kỳ, phân công", 415, 310)
p3 = P("3", "Xử lý case", 200, 430)
p4 = P("4", "Ra quyết định", 660, 430)
D4 = ST("D4", "Liên lạc và minh chứng", 415, 420)
D5 = ST("D5", "Nhận xét và quyết định", 415, 500)
D6 = ST("D6", "Nhật ký audit", 415, 590)
p6 = P("6", "Cấu hình vận hành", 660, 625)
D7 = ST("D7", "Tham số", 415, 705)
A = lambda s, t, l="", ex="", pts=None: d.edge(s, t, l, "arrow", extra=ex, pts=pts)
A(ml, p7, "dự đoán"); A(p7, D2, "lưu điểm"); A(p7, D3, "case PENDING", "exitX=0.2;exitY=1;entryX=0.9;entryY=0;")
A(nv, p1, "đăng nhập", "exitX=0.5;exitY=0;entryX=0;entryY=0.5;"); A(ql, p1, "đăng nhập", "exitX=1;exitY=0.5;entryX=1;entryY=0.2;", pts=[(1050, 328), (1050, 15)])
A(p1, D1, "", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
A(nv, p2, "lọc, nhận đơn", "exitX=0.8;exitY=0;entryX=0;entryY=0.5;"); A(p2, nv, "hàng đợi, chi tiết", "exitX=0.2;exitY=1;entryX=1;entryY=0.2;")
A(D2, p2, "điểm, yếu tố", "exitX=0;exitY=0.5;entryX=1;entryY=0.2;"); A(p2, D3, "phân công", "exitX=1;exitY=0.8;entryX=0.2;entryY=0;")
A(ql, p2, "giao / chuyển đơn", "exitX=0;exitY=0.2;entryX=1;entryY=0.6;")
A(D3, p5, "case, SLA", "exitX=1;exitY=0.3;entryX=0;entryY=0.8;"); A(p5, ql, "tổng quan, lịch sử", "exitX=1;exitY=0.7;entryX=0;entryY=0.5;")
A(D6, p5, "audit", "exitX=1;exitY=0.3;entryX=1;entryY=0.8;", pts=[(840, 600), (840, 279)])
A(nv, p3, "liên lạc, đóng case", "exitX=0.5;exitY=1;entryX=0;entryY=0.5;")
A(p3, D3, "trạng thái", "exitX=1;exitY=0.15;entryX=0.3;entryY=1;"); A(p3, D4, "lần liên lạc", "exitX=1;exitY=0.4;entryX=0;entryY=0.5;")
A(p3, D5, "nhận xét", "exitX=1;exitY=0.8;entryX=0;entryY=0.5;"); A(p3, D6, "audit", "exitX=0.7;exitY=1;entryX=0;entryY=0.5;")
A(D7, p3, "max_contact", "exitX=0;exitY=0.5;entryX=0.3;entryY=1;")
A(ql, p3, "mở lại", "exitX=0.7;exitY=1;entryX=0.1;entryY=1;", pts=[(970, 790), (215, 790)])
A(ql, p4, "quyết định", "exitX=0.3;exitY=1;entryX=1;entryY=0.3;"); A(D4, p4, "lịch sử liên lạc", "exitX=1;exitY=0.5;entryX=0;entryY=0.3;")
A(p4, D5, "quyết định mới", "exitX=0;exitY=0.8;entryX=1;entryY=0.5;"); A(p4, D6, "audit", "exitX=0.3;exitY=1;entryX=1;entryY=0.3;")
A(ql, p6, "tham số mới", "exitX=0.5;exitY=1;entryX=1;entryY=0.5;"); A(p6, D7, "phiên bản mới", "exitX=0.3;exitY=1;entryX=1;entryY=0.5;")
save(d, "dfd-muc-0")


# ======================= DFD mức 1 =========================================
def dfd1(name, ents, procs, stores, flows):
    d = D(name); ids = {}
    for k, (t, x, y) in ents.items():
        ids[k] = d.node(t, x, y, 130, 50, "ext")
    for k, (t, x, y) in procs.items():
        ids[k] = d.node(f"<b>{k}</b><hr>{t}", x, y, 150, 70, "proc")
    for k, (t, x, y) in stores.items():
        ids[k] = d.node(f"<b>{k}</b> &nbsp;|&nbsp; {t}", x, y, 180, 32, "store")
    for f in flows:
        s, t, l = f[:3]
        d.edge(ids[s], ids[t], l, "arrow", extra=f[3] if len(f) > 3 else "")
    save(d, name)


dfd1("dfd-1-hang-doi",
     {"NV": ("Nhân viên CSKH", 0, 120), "QL": ("Quản lý", 760, 120)},
     {"2.1": ("Lọc và sắp xếp hàng đợi", 200, 0), "2.2": ("Xem chi tiết đơn", 200, 230),
      "2.3": ("Nhận đơn", 200, 380), "2.4": ("Giao / chuyển đơn", 560, 380)},
     {"D2": ("Kết quả dự đoán", 440, 20), "D3": ("Case, chu kỳ, phân công", 380, 160),
      "D7": ("Tham số (capacity)", 380, 300), "D6": ("Nhật ký audit", 380, 500), "D1": ("Người dùng", 600, 270)},
     [("NV", "2.1", "bộ lọc, cách sắp xếp", "exitX=0.5;exitY=0;entryX=0;entryY=0.5;"), ("2.1", "NV", "trang kết quả", "exitX=0;exitY=0.9;entryX=0.8;entryY=0;"),
      ("D2", "2.1", "điểm, mức rủi ro"), ("D3", "2.1", "trạng thái, SLA", "exitX=0.2;exitY=0;entryX=1;entryY=0.9;"),
      ("NV", "2.2", "mã đơn", "exitX=0.5;exitY=1;entryX=0;entryY=0.5;"), ("D3", "2.2", "chu kỳ, liên lạc", "exitX=0;exitY=0.8;entryX=1;entryY=0.3;"),
      ("NV", "2.3", "lệnh Nhận", "exitX=0.2;exitY=1;entryX=0;entryY=0.5;"), ("D7", "2.3", "capacity", "exitX=0;exitY=0.8;entryX=1;entryY=0.3;"),
      ("2.3", "D3", "IN_PROGRESS + assignment", "exitX=0.9;exitY=0;entryX=0.3;entryY=1;"), ("2.3", "D6", "audit CLAIM", "exitX=0.7;exitY=1;entryX=0;entryY=0.5;"),
      ("QL", "2.4", "nhân viên, lý do, vượt capacity", "exitX=0.5;exitY=1;entryX=0.7;entryY=0;"), ("D1", "2.4", "tải việc", "exitX=0.7;exitY=1;entryX=0.4;entryY=0;"),
      ("2.4", "D3", "assignment mới", "exitX=0;exitY=0.2;entryX=0.9;entryY=1;"), ("2.4", "D6", "audit ASSIGN / OVERRIDE", "exitX=0.5;exitY=1;entryX=1;entryY=0.5;")])

dfd1("dfd-1-xu-ly-case",
     {"NV": ("Nhân viên CSKH", 0, 200), "QL": ("Quản lý", 800, 420)},
     {"3.1": ("Ghi nhận liên lạc", 200, 60), "3.2": ("Tải minh chứng", 200, 0), "3.3": ("Hoàn tất / bỏ qua", 200, 330),
      "3.4": ("Tự đóng UNREACHABLE", 620, 60), "3.5": ("Mở lại case", 620, 420), "3.6": ("Thêm nhận xét", 200, 460)},
     {"D4": ("Liên lạc và minh chứng", 420, 0), "D3": ("Case, chu kỳ, phân công", 420, 230),
      "D7": ("Tham số", 640, 180), "D5": ("Nhận xét và quyết định", 420, 540), "D6": ("Nhật ký audit", 420, 330)},
     [("NV", "3.2", "tệp PNG/JPG/PDF", "exitX=0.5;exitY=0;entryX=0;entryY=0.5;"), ("3.2", "D4", "tệp đã kiểm tra"),
      ("NV", "3.1", "thời điểm, kênh, kết quả", "exitX=0.8;exitY=0;entryX=0;entryY=0.7;"), ("3.1", "D4", "lần liên lạc", "exitX=1;exitY=0.3;entryX=0.2;entryY=1;"),
      ("3.1", "3.4", "không liên lạc được", "exitX=1;exitY=0.7;entryX=0;entryY=0.7;"), ("D7", "3.4", "max_contact", "exitX=0.6;exitY=0;entryX=0.5;entryY=1;"),
      ("3.4", "D3", "SKIPPED / UNREACHABLE", "exitX=0.2;exitY=1;entryX=0.9;entryY=0;"),
      ("NV", "3.3", "kết quả hoặc lý do", "exitX=0.5;exitY=1;entryX=0;entryY=0.5;"), ("3.3", "D3", "đóng case, trả slot", "exitX=0.9;exitY=0;entryX=0.2;entryY=1;"),
      ("3.3", "D6", "audit", "exitX=1;exitY=0.6;entryX=0;entryY=0.5;"),
      ("QL", "3.5", "lý do, xác nhận xem xét"), ("3.5", "D3", "chu kỳ mới, PENDING", "exitX=0.3;exitY=0;entryX=0.9;entryY=1;"), ("3.5", "D6", "audit REOPEN", "exitX=0;exitY=0.3;entryX=1;entryY=0.5;"),
      ("NV", "3.6", "nội dung", "exitX=0.3;exitY=1;entryX=0;entryY=0.5;"), ("3.6", "D5", "nhận xét", "exitX=1;exitY=0.7;entryX=0;entryY=0.5;")])

dfd1("dfd-1-quyet-dinh",
     {"QL": ("Quản lý", 0, 160)},
     {"4.1": ("Lấy case chờ quyết định", 220, 0), "4.2": ("Ghi quyết định", 220, 160), "4.3": ("Ghi chú cho mô hình", 220, 320)},
     {"D3": ("Case, chu kỳ, phân công", 470, 20), "D4": ("Liên lạc và minh chứng", 470, 80), "D5": ("Nhận xét và quyết định", 470, 190),
      "D6": ("Nhật ký audit", 470, 300)},
     [("QL", "4.1", "mở trang Quyết định", "exitX=0.5;exitY=0;entryX=0;entryY=0.5;"), ("D3", "4.1", "case đóng, needs_decision"), ("D4", "4.1", "lịch sử liên lạc", "exitX=0;exitY=0.5;entryX=1;entryY=0.8;"),
      ("4.1", "QL", "danh sách, chi tiết", "exitX=0.3;exitY=1;entryX=1;entryY=0.2;"),
      ("QL", "4.2", "quyết định, lý do, bước tiếp, hạn"), ("4.2", "D5", "quyết định (chỉ thêm)"), ("4.2", "D6", "audit DECISION", "exitX=1;exitY=0.8;entryX=0;entryY=0.3;"),
      ("QL", "4.3", "ghi chú", "exitX=0.5;exitY=1;entryX=0;entryY=0.5;"), ("4.3", "D6", "audit MODEL_NOTE", "exitX=1;exitY=0.4;entryX=0;entryY=0.8;")])

# ======================= Use case ==========================================
d = D("use-case")
d.node("Hệ thống Hidden Dissatisfaction", 150, 0, 790, 790, "boundary")
row = lambda i: 40 + i * 68
U = lambda t, x, i, st="uc", w=160, h=48, dy=0: d.node(t, x, row(i) + dy, w, h, st)
spec = d.node("Nhân viên CSKH", 50, row(0.5) - 15, 40, 80, "actor")
user = d.node("Người dùng", 50, row(6.5) - 15, 40, 80, "actor")
mgr = d.node("Quản lý", 1010, 300, 40, 80, "actor")
mlx = d.node("Quy trình chấm<br>điểm ML", 1010, 700, 40, 80, "actor")
s1 = U("Nhận đơn", 190, 0); s2 = U("Ghi nhận liên lạc", 190, 1); s3 = U("Tải minh chứng", 470, 1, w=140)
shared = ["Đăng nhập", "Đăng xuất", "Xem hồ sơ, đổi ngôn ngữ", "Xem Risk Queue", "Xem chi tiết đơn", "Thêm nhận xét", "Hoàn tất case", "Bỏ qua case"]
sh = [U(t, 190, 3 + i) for i, t in enumerate(shared)]
flt = U("Tìm kiếm, lọc, sắp xếp", 470, 6, w=150)
mg = ["Xem tổng quan rủi ro", "Giao / chuyển đơn", "Mở lại case", "Ghi quyết định", "Ghi chú cho mô hình", "Xem lịch sử thao tác", "Cấu hình tham số"]
mm = [d.node(t, 750, 40 + i * 92, 160, 50, "ucm") for i, t in enumerate(mg)]
ovr = d.node("Vượt capacity", 560, 200, 130, 44, "ucm")
seed = d.node("Nạp kết quả dự đoán", 750, 715, 160, 50, "ucm")
for t in (s1, s2):
    d.edge(spec, t, "", "line")
for t in sh:
    d.edge(user, t, "", "line")
for t in mm:
    d.edge(mgr, t, "", "line")
d.edge(mlx, seed, "", "line")
d.edge(s3, s2, "«extend»", "dashed", extra="verticalAlign=bottom;labelBackgroundColor=none;", off=(0, -4))
d.edge(flt, sh[3], "«extend»", "dashed", extra="verticalAlign=bottom;labelBackgroundColor=none;", off=(0, -4))
d.edge(ovr, mm[1], "«extend»", "dashed", extra="labelBackgroundColor=#f4f4f4;")
d.edge(spec, user, "", "inherit", extra="edgeStyle=orthogonalEdgeStyle;exitX=0;exitY=0.5;entryX=0;entryY=0.5;", pts=[(18, 99), (18, 507)])
d.edge(mgr, user, "", "inherit", extra="edgeStyle=orthogonalEdgeStyle;exitX=1;exitY=0.5;entryX=0;entryY=0.5;", pts=[(1110, 340), (1110, 830), (18, 830), (18, 507)])
save(d, "use-case")

# ======================= Vòng đời case =====================================
d = D("vong-doi-case")
st0 = d.node("", 0, 92, 26, 26, "start")
p = d.node("PENDING<br><span style='font-weight:normal;font-size:10px'>chờ nhận / chờ giao</span>", 80, 75, 150, 60, "state")
ip = d.node("IN_PROGRESS<br><span style='font-weight:normal;font-size:10px'>đang có người giữ</span>", 340, 75, 150, 60, "state")
co = d.node("COMPLETED<br><span style='font-weight:normal;font-size:10px'>HAS_ISSUE / NO_ISSUE / DUPLICATE</span>", 610, 0, 190, 60, "state", extra="fillColor=#d5e8d4;strokeColor=#82b366;")
sk = d.node("SKIPPED<br><span style='font-weight:normal;font-size:10px'>UNREACHABLE / REFUSED / ...</span>", 610, 150, 190, 60, "state", extra="fillColor=#f5f5f5;strokeColor=#666666;")
d.edge(st0, p, "seed từ dự đoán", "arrow")
d.edge(p, ip, "claim (NV) / assign (QL)", "arrow")
d.edge(ip, co, "complete", "arrow")
d.edge(ip, sk, "skip / tự đóng khi hết lượt", "arrow")
d.edge(ip, ip, "reassign, liên lạc", "flow", extra="exitX=0.3;exitY=1;entryX=0.7;entryY=1;", pts=[(385, 180), (445, 180)])
d.edge(co, p, "reopen (QL) → chu kỳ mới", "flow", pts=[(705, -40), (155, -40)], extra="exitX=0.5;exitY=0;entryX=0.5;entryY=0;")
d.edge(sk, p, "reopen (QL)", "flow", pts=[(705, 250), (155, 250)], extra="exitX=0.5;exitY=1;entryX=0.5;entryY=1;")
save(d, "vong-doi-case")

# ======================= Kiến trúc =========================================
d = D("kien-truc")
LB = "verticalAlign=bottom;labelBackgroundColor=none;"
d.node("Máy người dùng", 0, 0, 250, 320, "group")
br = d.node("<b>Trình duyệt</b><br>9 trang HTML, CSS, JavaScript<br>api.js gửi AJAX (XMLHttpRequest)<br>nhận JSON, lưu JWT", 15, 40, 220, 120, "rbox")
d.node("Giao diện Việt / Anh, dùng được trên máy tính, máy tính bảng, điện thoại", 15, 200, 220, 80, "note")
d.node("Docker Compose (máy chủ)", 360, 0, 690, 470, "group")
fe = d.node("<b>frontend</b> (Nginx)<br>phục vụ trang tĩnh,<br>chuyển /api/v1 sang API", 380, 45, 190, 110, "rbox")
api = d.node("<b>api</b> (FastAPI, Python)<br>23 endpoint nghiệp vụ,<br>kiểm tra quyền và quy tắc,<br>trả JSON", 690, 40, 220, 120, "rbox")
ev = d.node("Kho tệp minh chứng", 940, 230, 100, 70, "datastore")
pg = d.node("<b>postgres</b> (PostgreSQL 16)<br>schema <b>app</b>: nghiệp vụ<br>schema <b>ml</b>: dự đoán", 690, 230, 220, 100, "datastore")
mig = d.node("<b>migrate</b><br>V001 đến V022", 400, 245, 150, 70, "rbox")
job = d.node("Quy trình ML (theo lô):<br>dbt, huấn luyện, chấm điểm", 400, 370, 220, 70, "rbox")
d.edge(br, fe, "HTTP :4200", "flow", extra="exitX=1;exitY=0.4;entryX=0;entryY=0.4;" + LB, off=(0, -6))
d.edge(fe, api, "/api/v1/*", "flow", extra="exitX=1;exitY=0.5;entryX=0;entryY=0.5;" + LB, off=(0, -6))
d.edge(api, pg, "SQL, user app_api", "flow", extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;align=left;labelPosition=right;spacingLeft=8;labelBackgroundColor=none;")
d.edge(api, ev, "tệp", "flow", extra="exitX=1;exitY=0.5;entryX=0.5;entryY=0;labelBackgroundColor=none;", pts=[(990, 100)], pos=-0.3, off=(0, -10))
d.edge(mig, pg, "tạo bảng", "flow", extra="exitX=1;exitY=0.5;entryX=0;entryY=0.5;" + LB, off=(0, -6))
d.edge(job, pg, "ghi snapshot dự đoán", "flow", extra="exitX=1;exitY=0.5;entryX=0.5;entryY=1;" + LB, pts=[(800, 405)], pos=-0.3, off=(0, -6))
save(d, "kien-truc")
print("other done")

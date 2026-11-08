"""Vẽ lại FDD và sơ đồ ngữ cảnh cho gọn, chữ to, đường thẳng."""
from pathlib import Path
from dio import D
OUT = Path(__file__).parent / "drawio"
F = "fontFamily=Helvetica;html=1;whiteSpace=wrap;"

# ============================ FDD (trang ngang) ============================
d = D("fdd")
groups = [
    ("1. Quản lý tài khoản", ["1.1 Đăng nhập", "1.2 Đăng xuất", "1.3 Xem hồ sơ", "1.4 Đổi ngôn ngữ"]),
    ("2. Quản lý hàng đợi", ["2.1 Xem Risk Queue", "2.2 Tìm kiếm, lọc", "2.3 Xem chi tiết đơn", "2.4 Nhận đơn", "2.5 Giao, chuyển đơn"]),
    ("3. Xử lý case", ["3.1 Ghi liên lạc", "3.2 Tải minh chứng", "3.3 Hoàn tất case", "3.4 Bỏ qua case", "3.5 Mở lại case", "3.6 Thêm nhận xét"]),
    ("4. Ra quyết định", ["4.1 Xem case chờ", "4.2 Ghi quyết định", "4.3 Ghi chú mô hình"]),
    ("5. Giám sát", ["5.1 Xem tổng quan", "5.2 Xem theo sản phẩm", "5.3 Xem lịch sử"]),
    ("6. Cấu hình", ["6.1 Xem tham số", "6.2 Tạo phiên bản", "6.3 Hẹn giờ hiệu lực"]),
    ("7. Nạp dự đoán", ["7.1 Nhận snapshot", "7.2 Tạo case mới"]),
]
W, G, GH, CH, CW, IND = 176, 16, 50, 38, 156, 20
total = len(groups) * W + (len(groups) - 1) * G
RW = 560
root = d.node("HỆ THỐNG HỖ TRỢ XỬ LÝ ĐƠN HÀNG<br>CÓ NGUY CƠ KHÔNG HÀI LÒNG ẨN", total / 2 - RW / 2, 0, RW, 64,
              F + "rounded=1;arcSize=10;fillColor=#ffffff;strokeColor=#222222;strokeWidth=2;fontStyle=1;fontSize=17;")
ybus, gy = 100, 136
LINE = "edgeStyle=none;html=1;endArrow=none;strokeColor=#5b7fa6;strokeWidth=1.5;"
for i, (g, kids) in enumerate(groups):
    x = i * (W + G); cx = x + W / 2
    gid = d.node(g, x, gy, W, GH, F + "rounded=1;arcSize=12;fillColor=#dae8fc;strokeColor=#5b7fa6;fontStyle=1;fontSize=15;")
    d.edge(root, gid, "", LINE, extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;", pts=[(total / 2, ybus), (cx, ybus)])
    bx = x + IND / 2
    for j, k in enumerate(kids):
        ky = gy + GH + 18 + j * (CH + 12)
        kid = d.node(k, x + IND, ky, CW, CH, F + "rounded=1;arcSize=10;fillColor=#ffffff;strokeColor=#9db3cc;align=left;spacingLeft=10;fontSize=14;")
        d.edge(gid, kid, "", LINE, extra=f"exitX={IND/2/W};exitY=1;entryX=0;entryY=0.5;", pts=[(bx, ky + CH / 2)])
(OUT / "fdd.drawio").write_text(d.xml())

# ============================ Ngữ cảnh ============================
d = D("dfd-ngu-canh")
PX, PY, PW, PH = 400, 170, 230, 200
EW, EH = 170, 90
cy = PY + PH / 2
ENT = F + "rounded=0;fillColor=#ffe6cc;strokeColor=#d79b00;fontStyle=1;fontSize=16;"
sys_ = d.node('<b style="font-size:18px">0</b><hr>Hệ thống hỗ trợ xử lý<br>đơn hàng có nguy cơ<br>không hài lòng ẩn', PX, PY, PW, PH,
              F + "rounded=1;arcSize=14;fillColor=#dae8fc;strokeColor=#6c8ebf;strokeWidth=2;fontSize=15;")
nv = d.node("Nhân viên CSKH", 0, cy - EH / 2, EW, EH, ENT)
ql = d.node("Quản lý", PX + PW + (PX - EW), cy - EH / 2, EW, EH, ENT)
ml = d.node("Quy trình chấm điểm ML<br><span style='font-weight:normal;font-size:13px'>(chạy theo lô)</span>", PX + PW / 2 - 130, -150, 260, 80, ENT)
AR = "edgeStyle=none;html=1;endArrow=block;endFill=1;strokeColor=#333333;strokeWidth=1.5;fontSize=13;fontFamily=Helvetica;labelBackgroundColor=none;align=center;"
dy = 26
yin, yout = cy - dy, cy + dy
ey = lambda y, top, h: round((y - top) / h, 4)
# Nhân viên <-> hệ thống
d.edge(nv, sys_, "Đăng nhập, bộ lọc, lệnh nhận đơn,<br>lần liên lạc, minh chứng,<br>hoàn tất / bỏ qua, nhận xét", AR,
       extra=f"exitX=1;exitY={ey(yin, cy-EH/2, EH)};entryX=0;entryY={ey(yin, PY, PH)};verticalAlign=bottom;", off=(0, -6))
d.edge(sys_, nv, "Hàng đợi ưu tiên, chi tiết đơn,<br>yếu tố rủi ro, SLA, slot còn lại,<br>thông báo kết quả", AR,
       extra=f"exitX=0;exitY={ey(yout, PY, PH)};entryX=1;entryY={ey(yout, cy-EH/2, EH)};verticalAlign=top;", off=(0, 6))
# Quản lý <-> hệ thống
d.edge(ql, sys_, "Giao / chuyển đơn, mở lại,<br>quyết định, ghi chú mô hình,<br>tham số mới", AR,
       extra=f"exitX=0;exitY={ey(yin, cy-EH/2, EH)};entryX=1;entryY={ey(yin, PY, PH)};verticalAlign=bottom;", off=(0, -6))
d.edge(sys_, ql, "Số liệu tổng quan, tải việc,<br>case chờ quyết định,<br>lịch sử thao tác", AR,
       extra=f"exitX=1;exitY={ey(yout, PY, PH)};entryX=0;entryY={ey(yout, cy-EH/2, EH)};verticalAlign=top;", off=(0, 6))
# ML -> hệ thống
d.edge(ml, sys_, "Điểm rủi ro theo sản phẩm và đơn,<br>yếu tố liên quan, ngưỡng,<br>phiên bản mô hình", AR,
       extra="exitX=0.5;exitY=1;entryX=0.5;entryY=0;align=left;labelPosition=right;spacingLeft=10;", off=(0, 0))
(OUT / "dfd-ngu-canh.drawio").write_text(d.xml())
print("ok")

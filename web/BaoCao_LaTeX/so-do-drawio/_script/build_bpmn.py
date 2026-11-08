from pathlib import Path
from dio import BPMN

OUT = Path(__file__).parent / "drawio"; OUT.mkdir(exist_ok=True)
NV, HT, QL = "Nhân viên CSKH", "Hệ thống", "Quản lý"


def save(d, name):
    (OUT / f"{name}.drawio").write_text(d.xml())


# 1. Đăng nhập ---------------------------------------------------------------
d = BPMN("bpmn-dang-nhap", "ĐĂNG NHẬP", ["Người dùng", HT], 7)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Mở trang đăng nhập, chọn ngôn ngữ, nhập tên đăng nhập và mật khẩu", 0, 1)
t2 = d.at("systask", "Kiểm tra ô trống, gửi POST /auth/login", 1, 2)
g1 = d.at("gw", "Đúng tài khoản?", 1, 3)
e1 = d.at("task", "Đọc thông báo sai tài khoản hoặc mật khẩu", 0, 3)
t3 = d.at("systask", "Tạo JWT, trả thông tin người dùng và vai trò", 1, 4)
g2 = d.at("gw", "Vai trò?", 1, 5)
t4 = d.at("task", "Vào trang Tổng quan", 0, 6.4)
t5 = d.at("task", "Vào Risk Queue", 1, 6.4)
for a, b, l in ((s, t1, ""), (t1, t2, ""), (t2, g1, ""), (g1, e1, "Không"), (g1, t3, "Đúng"), (t3, g2, ""),
                (g2, t4, "MANAGER"), (g2, t5, "SPECIALIST")):
    d.edge(a, b, l)
d.edge(e1, t1, "Nhập lại")
save(d, "bpmn-dang-nhap")

# 2. Nhận đơn ------------------------------------------------------------------
d = BPMN("bpmn-nhan-don", "NHẬN ĐƠN (CLAIM)", [NV, HT], 8)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Mở Risk Queue, lọc và chọn đơn cần xử lý", 0, 1)
t2 = d.at("task", "Bấm Nhận", 0, 2)
t3 = d.at("systask", "Kiểm tra: PENDING, chưa ai giữ, không phải HIGH, còn capacity", 1, 3, h=64)
g1 = d.at("gw", "Đơn được nhận?", 1, 4)
g2 = d.at("gw", "Còn chỗ?", 1, 5)
er = d.at("task", "Đọc thông báo lý do không nhận được", 0, 4.5)
t4 = d.at("systask", "Đổi sang IN_PROGRESS (khóa theo row_version), tạo assignment, ghi audit", 1, 6)
t5 = d.at("task", "Đơn hiện ở mục Đơn của tôi", 0, 7)
e = d.at("end", "Kết thúc", 0, 7.75)
for a, b, l in ((s, t1, ""), (t1, t2, ""), (t2, t3, ""), (t3, g1, ""), (g1, g2, "Có"), (g1, er, "Không"),
                (g2, t4, "Có"), (t4, t5, ""), (t5, e, "")):
    d.edge(a, b, l)
d.edge(g2, er, "Không", extra="exitX=0;exitY=0.5;entryX=0.5;entryY=1;")
x, y = d.c(0, 1)
d.edge(er, t1, "Chọn đơn khác", extra="exitX=0;exitY=0.5;entryX=0;entryY=0.5;horizontal=0;labelBackgroundColor=#ffffff;", pts=[d.side(4.5), d.side(1)])
save(d, "bpmn-nhan-don")

# 3. Giao / chuyển đơn ---------------------------------------------------------
d = BPMN("bpmn-giao-don", "GIAO / CHUYỂN ĐƠN", [QL, HT, NV], 9)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Mở đơn chờ giao (thường là HIGH) hoặc đơn cần chuyển người", 0, 1)
t2 = d.at("task", "Bấm Giao đơn / Chuyển người, chọn nhân viên, nhập lý do", 0, 2)
t3 = d.at("systask", "Kiểm tra vai trò, trạng thái, lý do", 1, 3)
g1 = d.at("gw", "Nhân viên đã đủ capacity?", 1, 4.1, w=140, h=72)
g2 = d.at("gw", "Đã tích Vượt capacity?", 1, 5.5, w=140, h=72)
t4 = d.at("task", "Nhận báo lỗi CAPACITY_FULL; tích Vượt capacity, ghi lý do", 0, 5.5, h=64)
t5 = d.at("systask", "Giải phóng assignment cũ, tạo assignment mới, ghi audit (kèm override nếu vượt)", 1, 6.9, h=64)
t6 = d.at("task", "Nhận đơn trong mục Đơn của tôi", 2, 7.9)
e = d.at("end", "Kết thúc", 2, 8.7)
for a, b, l in ((s, t1, ""), (t1, t2, ""), (t2, t3, ""), (t3, g1, ""), (g1, g2, "Đã đủ"), (g2, t5, "Đã tích"),
                (g2, t4, "Chưa"), (t6, e, "")):
    d.edge(a, b, l)
xr = d.x0 + 2 * d.laneh - 16
d.edge(g1, t5, "Còn chỗ", extra="exitX=1;exitY=0.5;entryX=1;entryY=0.5;horizontal=0;labelBackgroundColor=#ffffff;", pts=[(xr, d.c(1, 4.1)[1]), (xr, d.c(1, 6.9)[1])])
d.edge(t4, t3, "Gửi lại", extra="exitX=0;exitY=0.5;entryX=0;entryY=0.5;", pts=[d.side(5.5), d.side(3)], pos=0.55, off=(0, -10))
d.edge(t5, t6, "", extra="exitX=0.5;exitY=1;entryX=0;entryY=0.5;", pts=[(d.c(1, 6.9)[0], d.c(2, 7.9)[1])])
save(d, "bpmn-giao-don")

# 4. Ghi nhận liên lạc ---------------------------------------------------------
d = BPMN("bpmn-lien-lac", "GHI NHẬN LIÊN LẠC KHÁCH HÀNG", [NV, HT], 11)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Liên hệ khách qua điện thoại, email hoặc tin nhắn", 0, 1)
t2 = d.at("task", "Nhập thời điểm, kênh, kết quả, ghi chú, ngày hẹn", 0, 2)
g1 = d.at("gw", "Có minh chứng?", 0, 3)
t3 = d.at("systask", "Kiểm tra PNG/JPG/PDF, tối đa 3 tệp, mỗi tệp ≤ 5 MB; lưu tệp", 1, 3.9)
t4 = d.at("systask", "Kiểm tra giờ có múi giờ, không ở tương lai; lưu lần liên lạc, ghi audit", 1, 5)
g2 = d.at("gw", "Kết quả?", 1, 6)
t5 = d.at("task", "Hoàn tất đơn, chọn kết quả", 0, 7)
g3 = d.at("gw", "Hết lượt?", 1, 7.6)
t6 = d.at("systask", "Đã đủ max_contact lần: tự đóng SKIPPED / UNREACHABLE", 1, 9, h=64)
t7 = d.at("task", "Hẹn lần liên lạc sau (gợi ý theo retry_gap_days)", 0, 9)
e1 = d.at("end", "Kết thúc", 0, 10)
e2 = d.at("end", "Kết thúc", 1, 10)
for a, b, l in ((s, t1, ""), (t1, t2, ""), (t2, g1, ""), (t3, t4, ""), (g2, t5, "Liên lạc được"),
                (g2, g3, "Chưa được"), (g3, t6, "Đủ"), (g3, t7, "Chưa"), (t6, e2, ""), (t7, e1, ""), (t4, g2, "")):
    d.edge(a, b, l)
d.edge(g1, t3, "Có", pts=[(d.c(0, 3)[0], d.c(1, 3.9)[1])])
gx = d.x0 + 2 * d.laneh - 16
d.edge(g1, t4, "Không", pts=[(gx, d.c(0, 3)[1]), (gx, d.c(1, 5)[1])])
d.edge(t5, e1, "", pts=[d.side(7), d.side(10)])
save(d, "bpmn-lien-lac")

# 5. Đóng case -----------------------------------------------------------------
d = BPMN("bpmn-dong-case", "HOÀN TẤT HOẶC BỎ QUA CASE", [NV, HT, QL], 9)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Bấm Hoàn tất hoặc Bỏ qua trên đơn đang giữ", 0, 1)
g1 = d.at("gw", "Hoàn tất?", 0, 2)
t2 = d.at("task", "Chọn kết quả: Có vấn đề / Không có vấn đề / Trùng", 0, 3.1, h=62)
t3 = d.at("task", "Chọn lý do bỏ qua; chọn Khác thì bắt buộc ghi chú", 0, 4.3, h=62)
t4 = d.at("systask", "Kiểm tra đơn IN_PROGRESS và đúng người giữ", 1, 4.3)
g2 = d.at("gw", "Hợp lệ?", 1, 5.5)
er = d.at("task", "Đọc lỗi, dữ liệu giữ nguyên", 0, 5.5)
t5 = d.at("systask", "Đóng case, trả slot, ghi lịch sử trạng thái và audit", 1, 6.6)
t6 = d.at("task", "Xem đơn trong danh sách chờ Quyết định (nếu cần)", 2, 7.6)
e = d.at("end", "Kết thúc", 2, 8.5)
for a, b, l in ((s, t1, ""), (t1, g1, ""), (g1, t2, "Có"), (t4, g2, ""), (g2, er, "Không"), (g2, t5, "Có"), (t5, t6, ""), (t6, e, "")):
    d.edge(a, b, l)
d.edge(g1, t3, "Không", extra="exitX=0;exitY=0.5;entryX=0;entryY=0.5;", pts=[d.side(2), d.side(4.3)])
d.edge(t2, t4, "", extra="exitX=1;exitY=0.5;entryX=0.5;entryY=0;", pts=[(d.c(1, 4.3)[0], d.c(0, 3.1)[1])])
d.edge(t3, t4, "", extra="exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
save(d, "bpmn-dong-case")

# 6. Mở lại case ---------------------------------------------------------------
d = BPMN("bpmn-mo-lai", "MỞ LẠI CASE ĐÃ ĐÓNG", [QL, HT], 7)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Mở đơn đã COMPLETED hoặc SKIPPED", 0, 1)
t2 = d.at("task", "Bấm Mở lại, nhập lý do", 0, 2)
g1 = d.at("gw", "Cần xác nhận?", 1, 3)
t3 = d.at("task", "Đóng quá số ngày hoặc mở lại nhiều lần: xác nhận đã xem xét", 0, 3.9, h=64)
t4 = d.at("systask", "Tạo chu kỳ mới, về PENDING, bỏ người phụ trách, tính lại SLA, ghi audit", 1, 5)
t5 = d.at("task", "Đơn trở lại Risk Queue, chờ giao hoặc nhận", 0, 6)
e = d.at("end", "Kết thúc", 0, 6.75)
for a, b, l in ((s, t1, ""), (t1, t2, ""), (t2, g1, ""), (g1, t3, "Có"), (g1, t4, "Không"), (t5, e, "")):
    d.edge(a, b, l)
d.edge(t4, t5, "", extra="exitX=0.5;exitY=1;entryX=1;entryY=0.5;", pts=[(d.c(1, 5)[0], d.c(0, 6)[1])])
xl = d.x0 + d.laneh + 18
d.edge(t3, t4, "", extra="exitX=1;exitY=0.5;entryX=0;entryY=0.5;", pts=[(xl, d.c(0, 3.9)[1]), (xl, d.c(1, 5)[1])])
save(d, "bpmn-mo-lai")

# 7. Ra quyết định -------------------------------------------------------------
d = BPMN("bpmn-quyet-dinh", "GHI QUYẾT ĐỊNH CỦA QUẢN LÝ", [QL, HT], 7)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Mở trang Quyết định, chọn case đã đóng cần quyết định", 0, 1)
t2 = d.at("task", "Đọc lịch sử liên lạc, nhận xét, quyết định trước", 0, 2)
t3 = d.at("task", "Chọn quyết định, lý do, bước tiếp, người làm, hạn", 0, 3)
t4 = d.at("systask", "Kiểm tra case đã đóng, đủ trường bắt buộc, hạn không ở quá khứ", 1, 4)
g1 = d.at("gw", "Hợp lệ?", 1, 5)
er = d.at("task", "Đọc lỗi và sửa", 0, 5)
t5 = d.at("systask", "Lưu quyết định (chỉ thêm mới), cập nhật bước tiếp theo, ghi audit", 1, 6)
e = d.at("end", "Kết thúc", 1, 6.75)
for a, b, l in ((s, t1, ""), (t1, t2, ""), (t2, t3, ""), (t3, t4, ""), (t4, g1, ""), (g1, er, "Không"), (g1, t5, "Có"), (t5, e, "")):
    d.edge(a, b, l)
d.edge(er, t3, "", pts=[d.side(5), d.side(3)])
save(d, "bpmn-quyet-dinh")

# 8. Thay đổi tham số ----------------------------------------------------------
d = BPMN("bpmn-tham-so", "THAY ĐỔI THAM SỐ VẬN HÀNH", [QL, HT], 7)
s = d.at("start", "Bắt đầu", 0, 0)
t1 = d.at("task", "Mở Cài đặt, chọn tham số (SLA, capacity, max_contact...)", 0, 1)
t2 = d.at("task", "Nhập giá trị mới, thời điểm hiệu lực, lý do", 0, 2)
t3 = d.at("systask", "Kiểm tra miền giá trị và ràng buộc (capacity_warn < capacity)", 1, 3)
g1 = d.at("gw", "Hợp lệ?", 1, 4)
er = d.at("task", "Đọc lỗi và sửa", 0, 4)
t4 = d.at("systask", "Tạo phiên bản mới (append-only), ghi audit", 1, 5)
g2 = d.at("gw", "Hiệu lực ngay?", 1, 6)
t5 = d.at("task", "Theo dõi lịch hẹn; tự áp dụng khi tới giờ", 0, 6, w=150)
e = d.at("end", "Kết thúc", 1, 7.2)
for a, b, l in ((s, t1, ""), (t1, t2, ""), (t2, t3, ""), (t3, g1, ""), (g1, er, "Không"), (g1, t4, "Có"), (t4, g2, ""),
                (g2, e, "Ngay")):
    d.edge(a, b, l)
d.edge(g2, t5, "Hẹn giờ", pos=-0.55, off=(0, -10))
d.edge(er, t2, "", pts=[d.side(4), d.side(2)])
save(d, "bpmn-tham-so")
print("bpmn done")

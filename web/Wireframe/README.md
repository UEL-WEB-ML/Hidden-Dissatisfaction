# Wireframe - Hidden Dissatisfaction

> **Bản vẽ trên Figma:** https://www.figma.com/design/Hu5nSjxSduHLvmMiuIfukl/Wireframe-%E2%80%93-Hidden-Dissatisfaction?node-id=1003-3710
>
> Thư mục này là bản **code** (HTML, CSS, JavaScript) của cùng wireframe đó.
> Khi sửa một màn thì cập nhật cả hai bản cho khớp nhau.
> **05/10/2026:** bản code đã chỉnh theo BRD v3.0 và FRD v1.0, bản Figma chưa cập nhật theo.

Wireframe cho đồ án môn Phát triển Web Kinh doanh: hệ thống nhận diện và ưu tiên đơn hàng Olist
giao đúng hạn nhưng có nguy cơ bị đánh giá 1–2 sao (bất mãn ẩn).

**Đây là bản phác thảo để thống nhất bố cục và hành vi, chưa phải sản phẩm.** Dữ liệu trong `mock-data.js`
là dữ liệu giả; tên field chỉ để vẽ giao diện, ERD và API Document sẽ chốt sau (BRD mục 9).

## Cách xem

Mở `login.html` bằng trình duyệt, không cần cài gì. Mật khẩu đều là `123456`:

| Tên đăng nhập | Người | Vai | Vào màn | Dùng để thử |
|---|---|---|---|---|
| `nhanvien` | Trần Thị B | Specialist | Risk Queue | Đang giữ 3/5 đơn: nhận thêm để thấy cảnh báo ở đơn thứ 4, khoá ở đơn thứ 5 |
| `nhanvien2` | Lê Văn C | Specialist | Risk Queue | Đã đủ 5/5; đơn `2b4d6f8a` đã liên lạc đủ 3 lần |
| `quanly` | Phạm Văn D | Manager | Dashboard | Assign, reassign, override capacity, mở lại, ghi chú model, Audit History |

- Góc dưới trái có hai nút vàng: **"Ghi chú: bật/tắt"** và **"Chế độ trình bày"** (ẩn mọi phần chỉ dành cho nhóm; tắt bằng phím `` ` `` hoặc `?present=0`).
- Cuối mỗi trang có khung vàng **"Công cụ demo"**: ô "Xem với vai" để đổi người dùng nhanh và nút "Đặt lại dữ liệu mẫu".
  Khung này **không thuộc sản phẩm** (bản thật vai lấy từ tài khoản, Backend kiểm tra quyền) và ẩn cùng nút "Ẩn/hiện ghi chú".
- Thanh điều hướng theo vai: Specialist chỉ có Risk Queue (tab "Tất cả / Đơn của tôi" nằm trong màn);
  Manager có Dashboard, Risk Queue, Audit History. Mục "Order Detail" chỉ hiện khi đang xem một đơn.
- Thao tác (nhận đơn, hoàn tất, bỏ qua…) được lưu tạm trong trình duyệt (localStorage) nên chuyển màn không mất.
- Thời gian được giả lập cố định ở **04/06/2018 14:00** để SLA và aging luôn ra cùng một kết quả.
- Thu nhỏ cửa sổ để xem bố cục máy tính bảng (768px) và điện thoại (375px).
- Ô màu vàng là ghi chú cho BA/Frontend (có mã function FRD), không thuộc giao diện thật.

## Màn hình và function FRD

| File | Màn hình | Người dùng | Function FRD |
|---|---|---|---|
| `login.html` | Đăng nhập (tài khoản tạo sẵn) | Cả hai | – |
| `overview.html` | Risk Overview Dashboard | Manager | F01 |
| `index.html` | Risk Queue: summary banner, tìm và lọc, nhận xử lý, assign | Specialist, Manager | F02, F03, F05 |
| `order.html` | Order Detail: kết quả model, yếu tố liên quan, xử lý, liên lạc/retry, audit của đơn | Specialist, Manager | F04, F05, F06, F07, F08 |
| `audit.html` | Audit History (chỉ đọc) | Manager | F09 |

File dùng chung: `style.css`, `common.js` (nhãn, luật nghiệp vụ, hộp thoại), `mock-data.js` (dữ liệu giả + cấu hình ngưỡng).

### Bảng thuật ngữ giao diện (đề xuất, nhóm chốt)

| Mã BRD | Nhãn giao diện | | Thao tác | Nhãn giao diện |
|---|---|---|---|---|
| PENDING | Pending | | Nhận xử lý | Claim |
| IN_PROGRESS | In progress | | Giao đơn | Assign |
| COMPLETED | Completed | | Chuyển người | Reassign |
| SKIPPED | Skipped | | Hoàn tất / Bỏ qua | Complete / Skip |
| SLA quá hạn | Overdue | | Mở lại | Reopen |
| Escalation | Escalated | | Vượt capacity | Override capacity |

Nếu nhóm chọn giao diện tiếng Việt thì chỉ cần đổi các bảng nhãn trong `common.js` và chữ trên các trang theo cột tiếng Việt ở trên
(Giao đơn, Chuyển người…); không đổi luật nghiệp vụ.

## Thay đổi so với bản 01/10

- Trạng thái theo BRD 6.4: **Chờ nhận (PENDING) → Đang xử lý (IN_PROGRESS) → Hoàn tất (COMPLETED) / Bỏ qua (SKIPPED)**.
  Hoàn tất bắt buộc outcome, bỏ qua bắt buộc lý do, chỉ Manager được mở lại (bắt buộc lý do).
- Mức rủi ro viết theo BRD: HIGH / MEDIUM / LOW; có threshold version và model version.
- Bỏ màn **Action Tracking**: ghi nhận liên lạc chuyển vào Order Detail (F07), truy vết chuyển sang màn **Audit History** (F09).
- Risk Queue: summary banner (HIGH chờ nhận, đơn nên bắt đầu, đơn đang giữ/5), cột aging + SLA + assignee,
  sắp xếp score → SLA → aging, tải thêm, chip filter, tìm Order ID có kiểm tra định dạng, mô phỏng hai người cùng nhận một đơn.
- Capacity 5 đơn: cảnh báo từ đơn thứ 4, khoá khi đủ 5; Manager override phải tích xác nhận và ghi lý do.
- Liên lạc tối đa 3 lần, cách nhau 1 ngày làm việc; hết lượt thì khoá form và hướng dẫn bỏ qua.
- SLA: HIGH 4 giờ, MEDIUM 1 ngày, LOW 2 ngày; escalation khi nằm queue ≥ 2 ngày; cảnh báo khi đang xử lý ≥ 1 ngày không cập nhật.
- Dashboard: bộ lọc có Áp dụng/Đặt lại, 6 thẻ chỉ số, tỷ lệ hoàn tất/bỏ qua/không liên lạc được, phân bố theo score band,
  seller/ngành hàng, workload và slot còn lại, danh sách cần can thiệp, phân công/override gần đây; bấm vào số liệu để mở Queue đã lọc sẵn.
- Không có chỗ nào sửa risk score; Manager chỉ có "Ghi chú model review".

## Điểm cần nhóm chốt

- **Lệch BRD 3.2:** Manager cần xem "Tổng số risk orders theo thời gian", nhưng FRD F01 bỏ sót và Dashboard chưa có biểu đồ theo thời gian.
   Cần bổ sung vào FRD trước rồi mới vẽ.
- **Ngôn ngữ giao diện:** wireframe đang để tiếng Anh thống nhất (xem bảng thuật ngữ ở trên); nhóm chốt Anh hay Việt.

1. **Outcome "Không liên lạc được sau khi hết retry" (BRD 6.5) và luật "sau lần 3 chuyển SKIPPED" (BRD 6.6) chồng nhau.**
   Wireframe hiện cho cả hai: hướng dẫn chính là Bỏ qua, còn outcome kia chỉ chọn được khi đã đủ 3 lần.
2. Mở lại một case thì giữ hay đặt lại bộ đếm liên lạc? Wireframe đang giữ nguyên lịch sử và bộ đếm.
3. SLA tính từ lúc vào queue tới lúc đóng, hay chỉ tới lúc được nhận (first-touch)? Wireframe tính tới lúc đóng.
4. Danh mục lý do bỏ qua cần Product Owner duyệt.
5. Wireframe tính SLA theo giờ đồng hồ; bản thật cần business calendar (giờ làm việc, ngày lễ).

## Dữ liệu mỗi đơn (đề xuất, chưa chốt với bên ML)

```
order_id · risk_score · risk_level · top_factors · suggested_action · model_version · predicted_at · threshold_version
```

Hệ thống chỉ đưa ra gợi ý để ưu tiên kiểm tra. Mọi quyết định xử lý do người dùng đưa ra.

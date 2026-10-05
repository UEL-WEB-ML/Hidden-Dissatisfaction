# Prototype - Hidden Dissatisfaction

> **Bản vẽ trên Figma:** https://www.figma.com/design/Hu5nSjxSduHLvmMiuIfukl/Wireframe-%E2%80%93-Hidden-Dissatisfaction?node-id=1003-3710
>
> Thư mục này là **prototype** bằng code (HTML, CSS, JavaScript), phát triển từ wireframe Figma đó, bấm thử được như sản phẩm thật.
> Khi sửa một màn thì cập nhật cả hai bản cho khớp nhau.
> **05/10/2026:** bản code đã chỉnh theo BRD v3.0 và FRD v1.0, bản Figma chưa cập nhật theo.

Prototype cho đồ án môn Phát triển Web Kinh doanh: hệ thống nhận diện và ưu tiên đơn hàng Olist
giao đúng hạn nhưng có nguy cơ bị đánh giá 1–2 sao (bất mãn ẩn).

**Đây là bản phác thảo để thống nhất bố cục và hành vi, chưa phải sản phẩm.** Dữ liệu trong `js/mock-data.js`
là dữ liệu giả; tên field chỉ để vẽ giao diện, ERD và API Document sẽ chốt sau (BRD mục 9).

## Cách xem

Mở `html/login.html` bằng trình duyệt, không cần cài gì. Mật khẩu đều là `123456`:

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
| `html/login.html` | Đăng nhập (tài khoản tạo sẵn) | Cả hai | – |
| `html/overview.html` | Risk Overview Dashboard | Manager | F01 |
| `html/index.html` | Risk Queue: summary banner, tìm và lọc, nhận xử lý, assign | Specialist, Manager | F02, F03, F05 |
| `html/order.html` | Order Detail: kết quả model, yếu tố liên quan, xử lý, liên lạc/retry, audit của đơn | Specialist, Manager | F04, F05, F06, F07, F08 |
| `html/audit.html` | Audit History (chỉ đọc) | Manager | F09 |

File dùng chung: `css/style.css`, `js/common.js` (nhãn, luật nghiệp vụ, hộp thoại), `js/mock-data.js` (dữ liệu giả + cấu hình ngưỡng).

## Sửa theo review UI 05/10

- **Risk Queue gọn phía trên bảng:** chỉ hiện 4 ô lọc hay dùng (Order ID, mức rủi ro, trạng thái, SLA); score, ngày, người phụ trách,
  seller, ngành hàng, kết quả vào nút **"More filters"** (hiện số filter đang bật). Tab, số đơn và sắp xếp gộp một hàng.
  Ở 1280px (ẩn ghi chú) bảng bắt đầu ở khoảng 514px thay vì ~730px.
- **Một nút chính mỗi màn:** chỉ "Claim" trong ô "Start with" là nút đậm; nút trong bảng (Claim/Assign/Reassign/View) đều là nút viền.
  Dashboard: "Apply" chỉ đậm khi filter đã đổi mà chưa áp dụng.
- **Đỏ chỉ còn một nghĩa: Quá hạn SLA.** Mức rủi ro là icon ô vuông + cột sóng (3 cột HIGH, 2 MEDIUM, 1 LOW) kèm chữ; bỏ vạch màu đầu dòng;
  thanh score, biểu đồ phân bố, "Pending HIGH", capacity đầy dùng màu trung tính.
- **Order Detail:** "Xử lý" + "Liên lạc" gộp thành một cột thao tác (nút trạng thái → form ghi liên lạc → lịch sử → thông tin case);
  cột thao tác đứng đầu trên điện thoại. Kết quả model và bối cảnh đơn ở cột còn lại.
- **Trạng thái tải / lỗi:** chọn "Giả lập trạng thái" trong khung công cụ demo để xem khung xám khi tải và khối lỗi có nút "Retry"
  (Risk Queue và Dashboard).
- **Lỗi đo được:** chữ phụ/chữ nhạt đạt ≥ 4.5:1; mọi chữ ≥ 12px; nút, ô chọn, ô nhập cao ≥ 44px trên màn hẹp/cảm ứng.
- **Tương tác:** hộp thoại đóng bằng Esc, giữ focus bên trong, đóng xong trả focus về nút đã bấm; thông báo lỗi đứng yên tới khi
  người dùng đóng (chỉ thông báo thành công tự tắt); tiêu đề cột Risk score / Aging / SLA bấm được để sắp xếp, có `aria-sort`;
  Order ID rút gọn có nút (biểu tượng) sao chép mã đầy đủ; Dashboard hiện "Filters changed, not applied yet" khi chưa bấm Apply.
- **Ngôn ngữ:** giao diện dùng tiếng Anh thống nhất (nhãn tập trung trong `js/common.js`), ghi chú vàng cho BA vẫn tiếng Việt.
- Xoá `actions.html` (màn Action Tracking đã bỏ từ bản 05/10, file cũ không còn chạy với dữ liệu mới).

### Vòng 2 (phản biện sau khi sửa)

- **Audit History dạng Kanban (mặc định):** cột = trạng thái hiện tại của đơn, thẻ = một đơn kèm các thao tác (3 gần nhất + "Show all"),
  cờ "Override". Nút "Table" giữ bảng theo thời gian làm cách xem phụ. Giá trị audit hiện bằng nhãn ("In progress", "unassigned") thay vì mã.
- **Risk Queue trên điện thoại:** bộ lọc gập sau nút "Filters" (chỉ ô Order ID luôn hiện), banner gọn ("Start with" một hàng,
  hai ô số liệu đứng cạnh nhau); đơn đầu tiên lên từ ~1.200px xuống ~780px. Thẻ đơn dạng nhãn | giá trị.
- **Bớt nhãn trong bảng:** bỏ mã seller (chỉ còn ngành hàng); nút sao chép dùng biểu tượng thay cho ký hiệu ⧉.
- **Order Detail:** nút đậm đổi theo bước. Chưa liên lạc được khách thì "Save attempt" đậm, "Complete" viền; liên lạc được hoặc hết lượt thì "Complete" đậm.
- **Dashboard:** "Pending HIGH" và "Overdue SLA" đứng đầu, to hơn, có link hành động; bỏ thẻ "Risk orders" (tổng số chuyển lên dòng dưới tiêu đề)
  và bỏ băng cảnh báo đỏ lặp số; "Needs attention" không lặp chữ HIGH; bảng Workload vừa khung.

### Vòng 3

- **Nhãn mức rủi ro kiểu priority của Linear:** icon ô vuông viền + 3 cột sóng (HIGH tô 3 cột, MEDIUM 2, LOW 1) kèm chữ; giữ màu cũ.
- **Số liệu để xử lý rõ hơn:** nhãn SLA chứa luôn con số ("1 h overdue", "45 min left") thay vì "Overdue" + dòng chữ xám nhỏ;
  score và aging dùng chữ số đều cột (tabular). Order Detail có dải 3 số liệu đầu cột thao tác: SLA, số lần liên lạc x/3 (kèm ngày hẹn),
  thời gian nằm queue.
- Audit History giữ dạng Kanban (nhóm đã duyệt).

### Vòng 4

- **Thanh điều hướng nền trắng** (trước là xám đen), mục đang mở gạch chân xanh dương; nút chính và lựa chọn đang bật dùng xanh dương.
- **Loại thao tác trong Audit có màu nền nhạt theo nhóm:** nhận/giao/chuyển người xanh ngọc, liên lạc chàm, hoàn tất xanh lá,
  bỏ qua xám nét đứt, mở lại/vượt capacity cam, ghi chú model hồng. Không dùng đỏ; override vẫn có viền đậm.

### Vòng 5–6

- **Thanh lọc và ô sắp xếp:** cùng chiều cao, bo góc, select có mũi tên riêng, ô Order ID có icon tìm kiếm; ô sắp xếp ghi gọn "Priority (default)".
- **Thẻ số liệu dùng chung** (Dashboard và banner Risk Queue): icon + nhãn ở trên, số to, dòng phụ, link hành động ở đáy thẻ;
  bỏ vạch màu dày trên đầu thẻ. Chỉ "Overdue SLA" có icon và số màu đỏ.
- **Khu vực người dùng:** avatar chữ viết tắt + tên + vai + nút "Sign out" có icon; trên điện thoại còn avatar + nút (trước đây bị ẩn mất).

### Vòng 7

- **Cột SLA:** chấm màu + con số dạng gọn ("1h overdue", "45m left"). Chỉ quá hạn có nền đỏ nhạt, chữ đỏ đậm; sắp hạn chữ vàng sẫm;
  còn hạn chữ xám. Không còn cả cột khối đỏ đặc.
- **Cột Aging:** dạng gọn "3d 5h"; nhãn "Escalated" là thẻ viền nhỏ cùng dòng nên mọi dòng cao bằng nhau.
- **Thẻ Dashboard:** 5 cột bằng nhau, cùng cỡ số, thẻ nào cũng có dòng phụ và link "View →" nên thẳng hàng.

### Vòng 8: hoàn thiện thẩm mỹ

- **Font Inter** (Google Fonts; hiển thị tiếng Việt tốt, chữ số đều cột). Không có mạng thì tự lùi về font hệ thống.
- **Trang đăng nhập mới:** cột giới thiệu nền xanh (logo, câu giới thiệu, 3 điểm chính) + thẻ đăng nhập; trên điện thoại chỉ còn thẻ.
  Nút điền nhanh tài khoản thử (chỉ trong prototype).
- **Khối nội dung đồng bộ với thẻ số liệu:** bo góc 12px, tiêu đề không gạch chân; biểu đồ phân bố mức rủi ro dạng thanh mảnh có %;
  dòng thời gian, bảng nhãn | giá trị, thanh so sánh được làm lại.
- **Tên ngành hàng dễ đọc:** "Bed, bath & table" thay cho `bed_bath_table` (bộ lọc vẫn dùng mã).
- **Chế độ trình bày:** ẩn ghi chú vàng, khung công cụ demo, gợi ý tài khoản thử. Bật/tắt bằng nút "Chế độ trình bày"
  ở góc dưới trái, phím `` ` `` (cạnh số 1), hoặc thêm `?present=1` / `?present=0` vào địa chỉ trang. Trình duyệt nhớ lựa chọn.
- Tiêu đề tab trình duyệt: "Risk Queue · Hidden Dissatisfaction" (bỏ chữ "— Wireframe"). Bỏ dòng link Figma ở cuối mỗi trang (link vẫn ở đầu README này).

### Bảng thuật ngữ giao diện (đề xuất, nhóm chốt)

| Mã BRD | Nhãn giao diện | | Thao tác | Nhãn giao diện |
|---|---|---|---|---|
| PENDING | Pending | | Nhận xử lý | Claim |
| IN_PROGRESS | In progress | | Giao đơn | Assign |
| COMPLETED | Completed | | Chuyển người | Reassign |
| SKIPPED | Skipped | | Hoàn tất / Bỏ qua | Complete / Skip |
| SLA quá hạn | Overdue | | Mở lại | Reopen |
| Escalation | Escalated | | Vượt capacity | Override capacity |

Nếu nhóm chọn giao diện tiếng Việt thì chỉ cần đổi các bảng nhãn trong `js/common.js` và chữ trên các trang theo cột tiếng Việt ở trên
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
- **Ngôn ngữ giao diện:** prototype đang để tiếng Anh thống nhất (xem bảng thuật ngữ ở trên); nhóm chốt Anh hay Việt.

1. **Outcome "Không liên lạc được sau khi hết retry" (BRD 6.5) và luật "sau lần 3 chuyển SKIPPED" (BRD 6.6) chồng nhau.**
   Prototype hiện cho cả hai: hướng dẫn chính là Bỏ qua, còn outcome kia chỉ chọn được khi đã đủ 3 lần.
2. Mở lại một case thì giữ hay đặt lại bộ đếm liên lạc? Prototype đang giữ nguyên lịch sử và bộ đếm.
3. SLA tính từ lúc vào queue tới lúc đóng, hay chỉ tới lúc được nhận (first-touch)? Prototype tính tới lúc đóng.
4. Danh mục lý do bỏ qua cần Product Owner duyệt.
5. Prototype tính SLA theo giờ đồng hồ; bản thật cần business calendar (giờ làm việc, ngày lễ).

## Dữ liệu mỗi đơn (đề xuất, chưa chốt với bên ML)

```
order_id · risk_score · risk_level · top_factors · suggested_action · model_version · predicted_at · threshold_version
```

Hệ thống chỉ đưa ra gợi ý để ưu tiên kiểm tra. Mọi quyết định xử lý do người dùng đưa ra.

# Prototype - Hidden Dissatisfaction

> **Bản vẽ trên Figma:** https://www.figma.com/design/Hu5nSjxSduHLvmMiuIfukl/Wireframe-%E2%80%93-Hidden-Dissatisfaction?node-id=1003-3710
>
> Thư mục này là **prototype** bằng code (HTML, CSS, JavaScript), phát triển từ wireframe Figma đó, bấm thử được như sản phẩm thật.
> Khi sửa một màn thì cập nhật cả hai bản cho khớp nhau.
> **13/10/2026:** bản code đã chỉnh theo BRD v4.0, FRD v2.0, API contract v0.2 và feedback giao diện 13/10. **14/10:** lên contract v0.3, thêm `js/config.js` + `BACKEND.md` để backend nối vào. **Bản Figma chưa cập nhật theo đợt này.**

Prototype cho đồ án môn Phát triển Web Kinh doanh: hệ thống nhận diện và ưu tiên đơn hàng Olist
giao đúng hạn nhưng có nguy cơ bị đánh giá 1–2 sao (bất mãn ẩn).

**Đây là bản phác thảo để thống nhất bố cục và hành vi, chưa phải sản phẩm.** Dữ liệu trong `js/mock-data.js`
là dữ liệu giả. Các trang lấy dữ liệu qua `js/api.js` theo đúng API contract v0.3 (repo `docs`, `docs/API_CONTRACT_olist_hidden_dissatisfaction.md`),
hiện đang chạy trên backend giả `js/mock-server.js`; khi backend thật xong thì chỉ sửa `js/config.js` (xem `BACKEND.md`).

## Cách xem

Mở `html/login.html` bằng trình duyệt, không cần cài gì. Góc trên thẻ đăng nhập có nút **VI | EN** để chọn ngôn ngữ. Mật khẩu đều là `123456`:

| Tên đăng nhập | Người | Vai | Vào màn | Dùng để thử |
|---|---|---|---|---|
| `nhanvien` | Trần Thị B | Specialist | Risk Queue | Đang giữ 3/5: đơn HIGH chỉ hiện "Chờ Manager giao"; nhận thêm đơn MEDIUM/LOW để thấy cảnh báo, khoá khi đủ |
| `nhanvien2` | Lê Văn C | Specialist | Risk Queue | Đã đủ 5/5; đơn `2b4d6f8a` đã liên lạc đủ 3 lần (form bị khoá) |
| `nhanvien3` | Nguyễn Văn A | Specialist | Risk Queue | Tài khoản đã lưu ngôn ngữ tiếng Việt: đăng nhập là tự chuyển sang tiếng Việt |
| `quanly` | Phạm Văn D | Manager | Dashboard | Giao/chuyển người, mở lại case (chu kỳ mới), quyết định, đổi tham số, Audit History |

- Góc dưới phải có hai nút vàng: **"Ghi chú: bật/tắt"** và **"Chế độ trình bày"** (ẩn mọi phần chỉ dành cho nhóm; tắt bằng phím `` ` `` hoặc `?present=0`).
- Cuối mỗi trang có khung vàng **"Công cụ demo"**: đổi tài khoản nhanh, giả lập mạng chậm/lỗi 500, "Đặt lại dữ liệu mẫu". Khung này **không thuộc sản phẩm**.
- Thanh điều hướng (cột dọc bên trái, trên điện thoại thành thanh ngang) theo vai: Specialist có Risk Queue, Chi tiết đơn, Liên lạc khách; Manager có Tổng quan, Risk Queue, Chi tiết đơn, Quyết định, Lịch sử thao tác, Cài đặt.
  Bấm avatar ở cuối thanh điều hướng để mở menu: Hồ sơ, Ngôn ngữ, Cài đặt tham số (Manager), Đăng xuất.
- Thao tác được backend giả lưu tạm trong trình duyệt (localStorage) nên chuyển màn không mất.
- Giờ máy chủ giả bắt đầu ở **04/06/2018 14:00** (mỗi thao tác cộng 1 phút) để SLA và aging luôn ra cùng một kết quả.
- Thu nhỏ cửa sổ để xem bố cục máy tính bảng (768px) và điện thoại (375px).
- Ô màu vàng là ghi chú cho BA/Frontend (có mã function FRD), không thuộc giao diện thật.

## Màn hình và function FRD

| File | Màn hình | Người dùng | Function FRD |
|---|---|---|---|
| `html/login.html` | Đăng nhập + chọn ngôn ngữ | Cả hai | F11 |
| `html/overview.html` | Risk Overview Dashboard: theo đơn / theo sản phẩm, biểu đồ số case vào queue theo ngày | Manager | F01 |
| `html/index.html` | Risk Queue: banner (ô "Đang giữ" là biểu đồ vòng), cột sản phẩm cần kiểm tra, tìm theo mã đơn hoặc mã sản phẩm | Specialist, Manager | F02, F03, F05 |
| `html/order.html` | Chi tiết đơn: ô tìm đơn + nút đơn trước/sau ở đầu trang, output tổng hợp + từng sản phẩm, nhận xét, bước tiếp theo, lịch sử trạng thái, mở lại case | Specialist, Manager | F04, F05, F06, F08 |
| `html/attempt.html` | Liên lạc khách: chọn đơn mình giữ, ghi lần liên lạc kèm minh chứng, lịch sử theo chu kỳ | Specialist (Manager chỉ xem) | F07 |
| `html/decision.html` | Quyết định: case cần quyết định, tóm tắt đơn + ML + việc nhân viên đã làm, form quyết định | Manager | *(feedback 13/10, chưa có mã)* |
| `html/settings.html` | Cài đặt tham số: giá trị đang hiệu lực, đổi có thời điểm hiệu lực + lý do, lịch sử phiên bản | Manager | F10 |
| `html/profile.html` | Hồ sơ: thông tin tài khoản, ngôn ngữ | Cả hai | F11 *(trang hồ sơ: feedback 13/10)* |
| `html/audit.html` | Audit History (chỉ đọc), thêm cột "Đổi tham số" | Manager | F09 |

## Cấu trúc code

| File | Vai trò |
|---|---|
| `js/config.js` | **Cấu hình duy nhất khi nối backend thật**: `BASE_URL`, `USE_MOCK`, `AUTH` (xem `BACKEND.md`) |
| `css/style.css` | Giao diện dùng chung |
| `js/api.js` | **Nơi duy nhất lấy và ghi dữ liệu.** Mỗi hàm ứng với một endpoint trong API contract |
| `js/common.js` | Ngôn ngữ (`L()`, `data-vi`), nạp người dùng + cấu hình (`boot()`), nhãn giao diện, định dạng, hộp thoại, thanh điều hướng + menu avatar |
| `js/mock-server.js` | Backend giả: trả lời đúng contract (JSON, mã lỗi 401/403/404/409/422), chứa luật nghiệp vụ BRD mục 6 |
| `js/mock-data.js` | Dữ liệu giả cho backend giả |
| `html/api-check.html` | Trang cho người làm backend tự so JSON của API thật với contract (không có trong menu) |
| `tools/mock-backend.js` | Backend giả chạy qua HTTP thật: `node tools/mock-backend.js` (cổng 8000) |

Luật nghiệp vụ (HIGH chỉ Manager giao, capacity, số lần liên lạc theo chu kỳ, chuyển trạng thái, bắt buộc lý do, tham số có phiên bản) và các số tính theo thời gian
(SLA, aging, escalation, số liệu Dashboard) nằm ở backend. Frontend chỉ hiển thị và báo lỗi backend trả về.

**Khi backend thật chạy:** chỉ sửa `js/config.js` (`USE_MOCK: false`, `BASE_URL`, `AUTH`), không sửa trang nào. Hướng dẫn đầy đủ: **`BACKEND.md`**.
(14/10: đã chạy thử toàn bộ qua HTTP thật bằng `tools/mock-backend.js`, gồm đăng nhập, upload minh chứng, và `api-check.html` 15/15 khớp.)

### Song ngữ

Mọi chữ trên giao diện có hai bản Việt/Anh. Chữ viết sẵn trong HTML có thuộc tính `data-vi="..."`; chữ do JavaScript tạo dùng `L("English", "Tiếng Việt")`
(`js/common.js`). Ngôn ngữ lưu trên máy và lưu theo tài khoản (`PATCH /me`). Mã trạng thái, score, ID, giá trị tham số, văn bản model sinh (`top_factors`)
và văn bản người dùng nhập giữ nguyên. Ô ghi chú vàng để tiếng Việt vì chỉ dành cho nhóm.

## Thay đổi so với bản 05/10

- **BRD v4.0 / FRD v2.0:** output ML theo từng sản phẩm, điểm đơn là điểm tổng hợp (`max-v1`), nhãn "Dữ liệu giả lập"; Specialist không tự nhận đơn HIGH;
  mở lại case tạo chu kỳ mới (reset bộ đếm liên lạc và SLA, giữ lịch sử); mọi con số vận hành lấy từ Parameter Configuration; Dashboard có chế độ xem
  theo sản phẩm, lọc theo mã sản phẩm, biểu đồ xu hướng; song ngữ Việt/Anh.
- **Feedback giao diện 13/10:**
  - Login: chọn ngôn ngữ.
  - Nhân viên: menu ở avatar (hồ sơ, ngôn ngữ, đăng xuất); "Chi tiết đơn" luôn có trên thanh điều hướng; tách phần liên lạc ra trang "Liên lạc khách"
    (chọn đơn được giao, ô minh chứng); Chi tiết đơn còn thông tin đơn, output ML, nhận xét của nhân viên và quản lý, bước tiếp theo + lịch sử trạng thái;
    ô "Đang giữ" ở Risk Queue thành biểu đồ vòng.
  - Quản lý: trang Cài đặt tham số; Chi tiết đơn có nút đậm "Mở lại case"; trang Quyết định.

- **Góp ý giảng viên 13/10 (Overview của Manager):** mỗi con số phải trả lời "rồi Manager làm gì" và cho thấy hệ thống giúp chăm sóc khách tốt hơn.
  - Đầu trang là khối **"Hôm nay cần làm"**: liệt kê việc theo mức ảnh hưởng tới khách (giao đơn HIGH, chuyển bớt việc cho người quá tải,
    nhắc đơn lâu không cập nhật, ra quyết định, seller dồn rủi ro), mỗi việc có lý do và nút đi thẳng tới chỗ xử lý.
  - Khối **"Chất lượng chăm sóc khách hàng"**: tỷ lệ khách được chủ động liên hệ, liên hệ lần đầu trong hạn SLA, thời gian tới lần liên hệ đầu,
    vấn đề phát hiện trước khi khách đánh giá.
  - 5 thẻ số ngang nhau gộp thành thanh **"Tiến độ xử lý"**. Biểu đồ theo ngày có câu nhận xét. Bảng khoảng score thu vào mục "Xem theo khoảng score".
  - API: `GET /dashboard` thêm `service` và `actions` (API contract v0.2, mục `GET /dashboard`).

- **Thiết kế lại giao diện 14/10 (chỉ đổi giao diện, logic và API giữ nguyên):**
  - Bộ màu mới khai báo một chỗ ở đầu `css/style.css` (biến `--ink-*`, `--accent`, `--high/--med/--low`…): thanh điều hướng màu mực, nền giấy ấm,
    màu nhấn tím. Đỏ / hổ phách / xanh lá vẫn chỉ dành cho mức rủi ro và quá hạn. Không dùng gradient.
  - Font Be Vietnam Pro (thiết kế cho tiếng Việt) + JetBrains Mono cho mã đơn.
  - Đăng nhập: bên trái là minh hoạ 3 đơn đều giao đúng hạn, một đơn bị model đánh dấu "dự báo 1–2 sao".
  - Overview viết lại cho trực quan, ít chữ: khối "đơn HIGH chưa có người nhận" dẫn mắt (kèm ai còn chỗ trống), 3 ô số có biểu đồ nhỏ, việc cần làm một dòng,
    biểu đồ ngày, vòng phân bố mức + thanh tiến độ, 4 vòng chất lượng chăm sóc, ô capacity từng nhân viên, thanh rủi ro theo seller. Bộ lọc ẩn sau nút "Bộ lọc".
  - Risk Queue: ô quan trọng nhất của banner nền mực (Manager: HIGH chờ giao; nhân viên: Nên bắt đầu). Bảng vừa khung từ 1280px.

## Điểm cần nhóm chốt

1. **Outcome "Không liên lạc được sau khi hết retry" (BRD 6.5) và luật "hết lượt thì chuyển SKIPPED" (BRD 6.6 mục 3) vẫn chồng nhau.**
   Prototype cho cả hai và không tự chuyển SKIPPED.
2. Trang Quyết định, nhận xét, minh chứng liên lạc, trang hồ sơ **chưa có trong BRD/FRD**: cần BA bổ sung (danh mục quyết định, minh chứng bắt buộc hay không, ai được nhận xét).
3. Tham số BRD 6.7 có nhưng F10-S02 chưa liệt kê (SLA nhận đơn, ngưỡng cảnh báo capacity, "sắp hạn", quá lâu không cập nhật, escalation, xem xét khi mở lại): có cho Manager sửa không.
4. Danh mục lý do bỏ qua cần Product Owner duyệt.
5. Prototype tính SLA theo giờ đồng hồ kể cả khi chọn "Giờ làm việc"; bản thật cần lịch làm việc, ngày lễ.

## Dữ liệu mỗi sản phẩm (đề xuất, chưa chốt với bên ML)

```
product_item_id · order_id · product_id · category · price · weight_g · photos
risk_score · risk_level · top_factors · suggested_action · model_version · predicted_at · synthetic_data_flag · data_source
```

Điểm của đơn = tổng hợp từ điểm sản phẩm theo `aggregation_rule` (đề xuất `max-v1`).

Hệ thống chỉ đưa ra gợi ý để ưu tiên kiểm tra. Mọi quyết định xử lý do người dùng đưa ra.

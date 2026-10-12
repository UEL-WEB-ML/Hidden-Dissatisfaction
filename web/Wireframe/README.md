# Wireframe - Hidden Dissatisfaction

> **Bản vẽ trên Figma:** https://www.figma.com/design/Hu5nSjxSduHLvmMiuIfukl/Wireframe-%E2%80%93-Hidden-Dissatisfaction?node-id=1003-3710
>
> Thư mục này là bản **code** (HTML, CSS, JavaScript) của cùng wireframe đó, viết sẵn để sau này sửa giao diện cho dễ.
> Muốn xem bản vẽ theo từng khổ màn hình (Desktop, iPad, Phone) thì mở link Figma ở trên.
> Khi sửa một màn thì cập nhật cả hai bản cho khớp nhau.

Bản wireframe bằng HTML, CSS, JavaScript cho đồ án môn Phát triển Web Kinh doanh:
hệ thống web hỗ trợ phát hiện và xử lý đơn hàng Olist giao đúng hạn nhưng có nguy cơ bị đánh giá thấp.

**Đây là bản phác thảo để thống nhất bố cục, chưa phải sản phẩm.** Dữ liệu trong `mock-data.js`
là dữ liệu giả, chưa nối với cơ sở dữ liệu hay mô hình dự đoán.

## Cách xem

Mở file `login.html` bằng trình duyệt (bấm đúp vào file), không cần cài gì. Tài khoản thử:

| Tên đăng nhập | Mật khẩu | Vai | Vào màn |
|---|---|---|---|
| `nhanvien` | `123456` | Nhân viên | Risk Queue |
| `quanly` | `123456` | Quản lý | Overview |

Mở thẳng `index.html` cũng được, khi đó xem như nhân viên.
Thu nhỏ cửa sổ để xem bố cục trên máy tính bảng (768px) và điện thoại (375px).

Cuối mỗi trang có dòng **"Bản vẽ wireframe trên Figma: mở trong tab mới"**. Bấm vào đó để xem bản vẽ trên Figma
(có sẵn 3 khổ Desktop, iPad, Phone và bản có ghi chú).

## Các màn hình hiện có

| File | Màn hình | Người dùng |
|---|---|---|
| `login.html` | Đăng nhập (không có đăng ký, tài khoản tạo sẵn) | Cả hai vai |
| `overview.html` | Overview (tổng quan): tiến độ nhóm, seller có nhiều đơn rủi ro | Quản lý |
| `index.html` | Risk Queue (hàng đợi đơn rủi ro) | Nhân viên, quản lý |
| `order.html` | Order Detail (chi tiết đơn và các yếu tố liên quan đến rủi ro) | Nhân viên, quản lý |
| `actions.html` | Action Tracking (ghi nhận và theo dõi xử lý) | Nhân viên, quản lý |

File dùng chung: `style.css` (giao diện), `common.js` (hàm dùng chung), `mock-data.js` (dữ liệu giả).

Ô màu vàng trên mỗi màn là chỗ ghi chú để BA viết đặc tả, không thuộc giao diện thật.

## Việc sẽ thay đổi sau khi chốt FRD

- Đã thêm màn Đăng nhập và Overview (01/10). Còn chờ FRD chốt bộ trạng thái xử lý và quyền ghi đè của quản lý.
- Đã bỏ màn Data Quality (01/10).
- Đổi số liệu theo BRD (88.163 đơn đúng hạn có đánh giá, 8.164 đơn bị chấm 1-2 sao).

## Dữ liệu mỗi đơn

Cấu trúc bên web đề xuất để nhận kết quả từ phần mô hình (chưa chốt với bên ML):

```
order_id · risk_score · risk_level · top_reasons · recommended_action · model_version
```

Hệ thống chỉ đưa ra gợi ý. Quyết định xử lý do người dùng đưa ra.

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

Mở file `index.html` bằng trình duyệt (bấm đúp vào file), không cần cài gì.
Thu nhỏ cửa sổ để xem bố cục trên máy tính bảng (768px) và điện thoại (375px).

Cuối mỗi trang có dòng **"Bản vẽ wireframe trên Figma: mở trong tab mới"**. Bấm vào đó để xem bản vẽ trên Figma
(có sẵn 3 khổ Desktop, iPad, Phone và bản có ghi chú).

## Các màn hình hiện có

| File | Màn hình | Người dùng |
|---|---|---|
| `index.html` | Danh sách đơn cần ưu tiên (Risk Queue) | Nhân viên xử lý đơn |
| `order.html` | Chi tiết đơn và các yếu tố liên quan đến rủi ro | Nhân viên xử lý đơn |
| `actions.html` | Ghi nhận và theo dõi xử lý | Nhân viên, quản lý |
| `data-quality.html` | Nguồn dữ liệu (sẽ bỏ) | |

File dùng chung: `style.css` (giao diện), `common.js` (hàm dùng chung), `mock-data.js` (dữ liệu giả).

Ô màu vàng trên mỗi màn là chỗ ghi chú để BA viết đặc tả, không thuộc giao diện thật.

## Việc sẽ thay đổi sau khi chốt FRD

- Thêm màn Đăng nhập (tài khoản tạo sẵn, không có đăng ký) với 2 vai: nhân viên và quản lý.
- Thêm màn Tổng quan cho quản lý.
- Bỏ màn Data Quality.
- Đổi số liệu theo BRD (88.163 đơn đúng hạn có đánh giá, 8.164 đơn bị chấm 1-2 sao).

## Dữ liệu mỗi đơn

Cấu trúc bên web đề xuất để nhận kết quả từ phần mô hình (chưa chốt với bên ML):

```
order_id · risk_score · risk_level · top_reasons · recommended_action · model_version
```

Hệ thống chỉ đưa ra gợi ý. Quyết định xử lý do người dùng đưa ra.

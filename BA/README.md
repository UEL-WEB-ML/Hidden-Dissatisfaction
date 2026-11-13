# BA as-built documentation

| Thuộc tính | Giá trị |
|---|---|
| Trạng thái | **AS-BUILT** |
| Ngày đối chiếu | 2026-11-02 |
| Nhánh review/testing | `dev` |
| Phạm vi | Static Prototype, FastAPI, PostgreSQL `app`/`ml`, workflow và local MLOps |

Thư mục này mô tả **hệ thống đang chạy**, không mô tả thiết kế mục tiêu. Các bản
BRD/FRD/API/Data Dictionary/ERD draft cũ đã bị xóa để tránh tồn tại hai source of
truth trong cùng repository.

## Thứ tự ưu tiên nguồn sự thật

1. PostgreSQL migrations và schema runtime.
2. FastAPI routes, Pydantic schemas và domain policy.
3. `frontend/prototype` và `frontend/prototype/js/api.js`.
4. Tests và runtime walkthrough.
5. Bộ tài liệu trong thư mục này.

Khi tài liệu trong thư mục này khác code hoặc migration, code/migration vẫn là
nguồn quyết định cho tới khi thay đổi được triển khai và kiểm thử.

## Danh mục

- [BRD](BRD.md): phạm vi nghiệp vụ và quy tắc đang hoạt động.
- [FRD](FRD.md): màn hình, chức năng và acceptance criteria as-built.
- [API Contract](API_CONTRACT.md): endpoint và DTO thực tế.
- [Data Dictionary](DATA_DICTIONARY.md): schema vật lý hiện tại.
- [ERD](ERD.md): quan hệ vật lý giữa các bảng chính.
- [Traceability](TRACEABILITY.md): UI → API → policy → database và kết quả kiểm tra hai vòng.

## Ranh giới quan trọng

- Hệ thống dùng Bearer JWT; cookie session chưa được triển khai.
- Training/scoring là batch thủ công, không có online training hay auto-retrain.
- Product-item là grain của prediction snapshot, nhưng chưa có model artifact thực
  được promote cho stack demo hiện tại.
- 100 đơn Olist trong local stack có context thật; score hiện tại là deterministic
  UI demo score, không phải model inference.
- `sla_calendar=BUSINESS_HOURS` được lưu và hiển thị nhưng phép tính SLA backend
  hiện vẫn dùng giờ liên tục.

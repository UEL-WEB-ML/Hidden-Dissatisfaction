# Tài liệu BA tổng hợp: hệ thống như đã xây dựng (as-built)

**Phạm vi.** Tài liệu này mô tả hệ thống **theo đúng codebase hiện tại** (branch `thesis`, cơ sở commit `6e8976f`/`25f190b`). Khi có khác biệt, tài liệu này **thay thế** cho BRD 4.2, FRD 2.2, API Contract 0.5, ERD và Data Dictionary 0.5 trong `docs/`. Mọi khẳng định đều có trích nguồn `file:dòng`, trong đó:

- `M/Vxxx` = `infra/postgres/migrations/Vxxx__*.sql`
- `S/` = `src/hidden_dissatisfaction/`
- `F/` = `frontend/hidden-dissatisfaction-frontend/src/app/`

Mục 10 liệt kê các chỗ tài liệu cũ không khớp với code.

---

## 1. Tổng quan

**Mục tiêu nghiệp vụ.** Hệ thống giúp bộ phận chăm sóc khách hàng (CSKH) tìm và xử lý sớm các đơn hàng đã giao đúng hạn nhưng có nguy cơ nhận đánh giá 1–2 sao. Mô hình học máy chấm điểm từng sản phẩm trong đơn. Điểm của đơn là điểm sản phẩm cao nhất (`max-v1`). Đơn được đưa vào hàng đợi rủi ro để nhân viên liên hệ khách, ghi nhận kết quả và để quản lý ra quyết định.

**Thành phần.**

| Thành phần | Công nghệ | Nguồn |
|---|---|---|
| Kho dữ liệu | PostgreSQL, gồm Bronze (nạp CSV) và dbt (Silver, Intermediate, Gold) | `M/V019`, `dbt/models/` |
| Huấn luyện và chấm điểm | Python, scikit-learn, CatBoost; dùng qua CLI | `S/interfaces/cli.py:22-105` |
| Backend | FastAPI, xác thực JWT | `S/api/app.py:120` |
| Frontend | Angular (Signal Desk) | `F/app.routes.ts:5-19` |
| Triển khai | Docker Compose gồm `postgres`, `migrate`, `api`, `frontend`. Profile `jobs` chạy `warehouse`, profile `quality` chạy `frontend-test` | `compose.yaml` |

**Trạng thái dữ liệu trên web.** Hiện web hiển thị **dữ liệu demo tổng hợp**, gồm 5 đơn `demo-1001`…`demo-1005` do `scripts/demo-seed.sh` tạo trực tiếp bằng SQL. Release được đánh dấu `SYNTHETIC_DEMO` và dùng ngưỡng 0,40/0,70. Mô hình thật đang ở trạng thái `EXPLORATORY_NON_CONFIRMATORY`, nên DB **không cho phép kích hoạt** (`M/V020:17-34`). Mã chấm điểm và đưa đơn vào hàng đợi đã có (`S/application/release_scoring.py`, `queue_seeding.py`), nhưng **chưa có lệnh CLI hay target Make nào gọi tới**.

---

## 2. Người dùng và phân quyền

Hệ thống có hai vai trò là `SPECIALIST` và `MANAGER` (`S/domain/auth.py:7-11`, `M/V003:5-11`). Vai trò gắn với tài khoản, người dùng không tự chọn.

| Thao tác | Specialist | Manager | Ghi chú |
|---|:-:|:-:|---|
| Xem hàng đợi, chi tiết đơn, banner tóm tắt, cấu hình | ✓ | ✓ | |
| **Nhận đơn (claim)** | ✓ | ✗ | Chỉ đơn PENDING, chưa có người nhận, **không phải HIGH** |
| **Giao / chuyển đơn (assign)** | ✗ | ✓ | Người nhận phải là Specialist đang hoạt động. Đây là cách duy nhất để đơn HIGH có người xử lý |
| Hoàn tất / bỏ qua | chỉ người được giao | ✓ mọi đơn | |
| Mở lại đơn (reopen) | ✗ | ✓ | |
| Bình luận | chỉ người được giao | ✓ | |
| Ghi chú mô hình (model note) | ✗ | ✓ | |
| Ghi lần liên lạc | **chỉ người đang được giao** | ✗ | |
| Tải lên minh chứng | ✓ | ✗ | |
| Tải xuống minh chứng | người tải lên hoặc người được giao | ✓ | |
| Quyết định của quản lý | ✗ | ✓ | |
| Dashboard, lịch sử kiểm toán, tham số | ✗ | ✓ | |
| **Sửa điểm hoặc mức rủi ro** | ✗ | ✗ | Không có API nào; DB chặn UPDATE |

Nguồn: `S/api/app.py:247,275,367`, `S/api/workflow_routes.py:173-331`, `S/infrastructure/postgres_workflow_commands.py:150,235,334,371`, `S/infrastructure/local_evidence_store.py:85`.

Frontend ẩn các nút ngoài quyền (`F/features/queue/queue.mappers.ts:12-13`, `F/features/order-detail/order-detail.component.ts:25-44`), nhưng backend vẫn kiểm tra lại mọi yêu cầu.

---

## 3. Màn hình (frontend)

| Route | Vai trò | Nội dung và thao tác |
|---|---|---|
| `/login` | công khai | Đăng nhập |
| `/queue` (mặc định) | cả hai | Hàng đợi rủi ro: lọc, tải lại, nhận đơn, giao đơn |
| `/orders/:id` | cả hai | Chi tiết đơn: yếu tố chính (top factors), các sản phẩm, dòng thời gian trạng thái, bình luận, quyết định gần nhất. Thao tác: nhận, giao, hoàn tất/bỏ qua, mở lại, bình luận, ghi chú mô hình, tải minh chứng |
| `/orders/:id/attempt` | cả hai (backend chỉ cho người được giao ghi) | Thêm lần liên lạc kèm dòng thời gian |
| `/orders/:id/decision` | Manager | Ghi quyết định kèm lịch sử quyết định |
| `/decisions` | Manager | Danh sách đơn cần quyết định |
| `/dashboard` | Manager | Tổng quan (chi tiết ở mục 7) |
| `/audit` | Manager | Lịch sử kiểm toán, chỉ đọc |
| `/parameters` | Manager | Giá trị hiện hành, lên lịch thay đổi, các thay đổi đã lên lịch, lịch sử phiên bản |
| `/profile` | cả hai | Hồ sơ |

Nguồn: `F/app.routes.ts:5-19`, `F/core/guards.ts:4-5`.

- **Thanh điều hướng:** các mục Overview, Audit, Parameters chỉ hiện với Manager. Thanh này **không có link tới `/decisions`** (`F/layout/app-shell.component.ts:8-14`).
- **Ngôn ngữ:** nút EN/VI lưu lựa chọn qua `PATCH /auth/me` và gửi kèm header `Accept-Language` (`F/core/interceptors.ts:13`). Tuy nhiên **nhãn giao diện đang ghi cứng tiếng Anh**, nên bấm nút chỉ đổi ngôn ngữ của thông báo lỗi từ backend (`S/api/app.py:~427`).

---

## 4. Vòng đời đơn rủi ro (case)

### 4.1 Trạng thái

`PENDING` và `IN_PROGRESS` là trạng thái mở; `COMPLETED` và `SKIPPED` là trạng thái đóng (`S/domain/workflow.py:19-20`, `M/V003:12-21`). Mỗi đơn có **đúng một case trong suốt vòng đời** (`order_id` UNIQUE).

```text
           seed (QUEUE_SEED)
                 │
                 ▼
            ┌─────────┐  claim (Specialist, không HIGH)   ┌─────────────┐
            │ PENDING │ ─────────────────────────────────▶ │ IN_PROGRESS │
            └─────────┘  assign (Manager, mọi mức)         └─────────────┘
                 ▲                                          │ complete(outcome)
                 │ reopen (Manager, bắt buộc lý do)         │ skip(reason)
                 │                                          │ liên lạc thứ max_contact không REACHED → tự SKIPPED/UNREACHABLE
            ┌────┴──────────────────┐ ◀──────────────────────┘
            │ COMPLETED / SKIPPED   │
            └───────────────────────┘
```

### 4.2 Luật chuyển trạng thái

| Chuyển | Ai | Điều kiện / dữ liệu bắt buộc | Lỗi |
|---|---|---|---|
| **Nhận** PENDING → IN_PROGRESS | Specialist | Đơn chưa có người nhận; không phải HIGH; số đơn đang xử lý nhỏ hơn `capacity`. Cập nhật có điều kiện theo `row_version`, nên khi 2 người cùng nhận thì người sau bị từ chối | 409 `ALREADY_CLAIMED`, 403 `HIGH_RISK_REQUIRES_ASSIGN`, 422 `CAPACITY_FULL` |
| **Giao / chuyển** đơn đang mở → IN_PROGRESS | Manager | Đơn phải đang mở; không giao lại cho đúng người cũ; chuyển người phải có lý do; vượt `capacity` phải đặt `override_capacity=true` kèm lý do (sinh thêm sự kiện kiểm toán OVERRIDE) | 409 `INVALID_STATE`, 422 `REASON_REQUIRED`, `CAPACITY_FULL` |
| **Hoàn tất** IN_PROGRESS → COMPLETED | người được giao / Manager | `outcome` ∈ {HAS_ISSUE, NO_ISSUE, DUPLICATE} | 422 |
| **Bỏ qua** IN_PROGRESS → SKIPPED | người được giao / Manager | `skip_reason` ∈ {UNREACHABLE, DUPLICATE, REFUSED, NOT_APPLICABLE, OTHER}; nếu chọn OTHER thì phải có ghi chú | 422 |
| **Mở lại** đơn đóng → PENDING | Manager | Luôn phải có lý do. Phải xác nhận thêm (`review_confirmed=true`) nếu đơn đã đóng quá `reopen_review_days` ngày, hoặc đã mở lại từ `reopen_review_times` lần trở lên | 422 `REVIEW_CONFIRMATION_REQUIRED` |

Nguồn: `S/domain/workflow.py:39-93,117-138`, `S/infrastructure/postgres_claim_case.py:60-66`, `S/infrastructure/postgres_workflow_commands.py:34-325`.

- **Khi mở lại:** hệ thống tạo chu kỳ mới (`cycle_no+1`) với hạn SLA mới; xóa người được giao, kết quả, lý do bỏ qua, ghi chú và thời điểm đóng; tăng `reopen_count`. Thời điểm vào hàng đợi lần đầu (`original_queued_at`) và lịch sử được giữ nguyên.
- **Ràng buộc ở DB:** chuyển trạng thái không bị DB kiểm tra mà do tầng ứng dụng đảm bảo. DB chỉ kiểm tra tập giá trị hợp lệ, khóa các cột snapshot, và yêu cầu prediction gắn với case phải đang ACTIVE (`M/V003:27-36`, `M/V014`).

### 4.3 Chu kỳ xử lý và SLA

| Khái niệm | Định nghĩa | Nguồn |
|---|---|---|
| Chu kỳ (cycle) | Mỗi lần đơn vào hàng đợi hoặc được mở lại. Mỗi case chỉ có một chu kỳ mở; chu kỳ chỉ được đóng một lần (đặt `ended_at`) | `M/V008:5-12` |
| Hạn SLA | `bắt đầu chu kỳ + sla_hours_{high, medium, low}`, tính **theo giờ đồng hồ**. Khi Manager đổi tham số SLA, tác vụ `recalculate-sla` ghi bản điều chỉnh vào `app.sla_adjustments` (bản mới nhất được dùng) | `S/domain/case_metrics.py:26-55`, `S/infrastructure/sla_recalculation.py` |
| Quá hạn / sắp hạn | Chỉ tính với đơn đang mở: `over` khi đã quá hạn; `soon` khi còn không quá `soon_hours` giờ | `case_metrics.py` |
| Leo thang (escalated) | Đơn đang mở đã nằm trong hàng đợi từ `aging_days` ngày trở lên, tính từ `original_queued_at` | `S/infrastructure/postgres_risk_queue.py:126` |
| Bị bỏ quên (stale) | Đơn IN_PROGRESS không được cập nhật trong `stale_hours` giờ | `case_metrics.py` |
| Cần quyết định | Đơn đã đóng nhưng chưa có quyết định của Manager | `case_metrics.py:83` |

---

## 5. Liên lạc khách hàng và minh chứng

- **Ai được ghi:** chỉ **người đang được giao** đơn, và chỉ khi đơn IN_PROGRESS có chu kỳ đang mở (`S/infrastructure/postgres_workflow_commands.py:360-470`).
- **Dữ liệu một lần liên lạc:**
  - kênh: `PHONE`, `EMAIL`, `MESSAGE` (khi lưu xuống DB, `MESSAGE` được ghi thành `CHAT`; `S/infrastructure/postgres_workflow_commands.py:32`);
  - kết quả: `REACHED`, `NO_ANSWER`, `CALLBACK`, `WRONG_NUMBER`;
  - thời điểm liên lạc: phải có múi giờ và không ở tương lai;
  - ngày hẹn liên lạc lại: không được trước thời điểm liên lạc;
  - ghi chú.
- **Giới hạn:** tối đa `max_contact` lần liên lạc mỗi chu kỳ; số thứ tự lần liên lạc đánh lại từ đầu ở mỗi chu kỳ (`M/V013:6-8`). Nếu lần cuối cùng không phải `REACHED`, đơn **tự động chuyển SKIPPED với lý do UNREACHABLE** (`S/domain/workflow.py:82`, `S/infrastructure/postgres_workflow_commands.py:469`).
- **Minh chứng:**
  - tối đa 3 tệp cho mỗi lần liên lạc, mỗi tệp từ 1 byte đến 5 MB, chỉ nhận PNG, JPG hoặc PDF;
  - loại tệp được nhận diện **theo chữ ký nội dung tệp**, không theo tên hay khai báo của client;
  - tệp phải do chính người ghi tải lên và chưa gắn với lần liên lạc nào;
  - tệp tải lên mà không được gắn sẽ bị tác vụ `purge-evidence` xóa sau 24 giờ.
  
  Nguồn: `S/domain/workflow.py:101-106,178-185`, `M/V013:12-22`, `S/infrastructure/evidence_cleanup.py`.
- **Quyết định của Manager:**
  - loại quyết định: `NO_FURTHER_ACTION`, `FOLLOW_UP_CUSTOMER`, `WORK_WITH_SELLER`, `REFER_AFTER_SALES`;
  - bắt buộc có lý do và bước tiếp theo; hạn xử lý không được ở quá khứ; người thực hiện (nếu có) phải là người dùng đang hoạt động;
  - quyết định chỉ được **thêm vào chu kỳ gần nhất**, không đổi trạng thái hay điểm, và **không bắt buộc đơn phải đã đóng** (`S/infrastructure/postgres_workflow_commands.py:485-534`).
- **Bình luận:** 1–1000 ký tự sau khi bỏ khoảng trắng hai đầu. Bình luận, lần liên lạc, minh chứng và quyết định đều **chỉ được thêm, không sửa hay xóa** (DB chặn bằng trigger, `M/V006:43-47`).

---

## 6. Tham số vận hành

Tham số có phiên bản và chỉ được thêm mới. Giá trị hiện hành là phiên bản mới nhất có `effective_at <= now`, nên đặt `effective_at` ở tương lai nghĩa là **lên lịch** thay đổi. Mỗi thay đổi bắt buộc có lý do và sinh sự kiện kiểm toán `PARAMETER_CHANGE`. Cùng lúc phải có `capacity_warn < capacity`.

Nguồn: `S/domain/parameters.py:27-103`, `S/infrastructure/postgres_parameters.py:89`, `M/V004`, `M/V011`.

| Khóa | Ý nghĩa | Giá trị khởi tạo | Khoảng hợp lệ (ứng dụng) | Được dùng? |
|---|---|---|---|---|
| `sla_hours_high` / `_medium` / `_low` | Hạn SLA theo mức rủi ro (giờ) | 4 / 24 / 48 | 1–720 | ✓ |
| `capacity` | Số đơn tối đa một Specialist xử lý cùng lúc | 5 | 1–20 | ✓ |
| `max_contact` | Số lần liên lạc tối đa mỗi chu kỳ | 3 | 1–10 | ✓ |
| `soon_hours` | Ngưỡng "sắp quá hạn" (giờ) | 2 | 1–720 | ✓ |
| `stale_hours` | Ngưỡng "bị bỏ quên" (giờ) | 24 | 1–720 | ✓ |
| `aging_days` | Ngưỡng leo thang (ngày) | 2 | 1–60 | ✓ |
| `reopen_review_days` / `reopen_review_times` | Khi nào mở lại cần xác nhận thêm | 7 / 2 | 1–60 / 1–10 | ✓ |
| `sla_calendar` | CALENDAR hoặc BUSINESS_HOURS | CALENDAR | enum | ✗ chưa dùng (luôn tính theo giờ đồng hồ) |
| `first_touch_hours` | Hạn liên lạc lần đầu | 2 | 1–720 | ✗ chỉ hiển thị |
| `retry_gap_days` | Khoảng cách tối thiểu giữa hai lần liên lạc | 1 | 1–60 | ✗ chỉ hiển thị |
| `capacity_warn` | Ngưỡng cảnh báo gần đầy | 4 | 1–20 | ✗ chỉ được kiểm tra `< capacity` |

DB cho phép khoảng rộng hơn (ví dụ `capacity` 1–1000); giới hạn chặt hơn nằm ở tầng ứng dụng.

---

## 7. Hàng đợi, tìm kiếm và dashboard

**Hàng đợi** (`S/infrastructure/postgres_risk_queue.py:21-23`, `S/domain/queue.py:12-78`).

- **Sắp xếp:**
  - mặc định: điểm giảm dần → hạn SLA gần nhất → thời điểm vào hàng đợi → mã đơn;
  - `sla`: hạn SLA tăng dần → điểm giảm dần;
  - `aging`: thời điểm vào hàng đợi đầu tiên tăng dần → điểm giảm dần.
- **Lọc:**
  - tiền tố mã đơn, hoặc đúng một mã sản phẩm-trong-đơn;
  - mức rủi ro; trạng thái (mặc định `OPEN` = PENDING + IN_PROGRESS); người được giao (`me`, `none`, hoặc id);
  - khoảng điểm 0–1; khoảng ngày; người bán; danh mục;
  - kết quả (`O:<outcome>`, `S:<skip>`); SLA (`over`, `soon`, `esc`, `stale`); `needs_decision`;
  - phân trang `limit` 1–100.
- **Banner tóm tắt** (`S/application/queue.py:51-73`):
  - đếm số đơn HIGH chờ xử lý, HIGH chờ và quá hạn, quá hạn, leo thang, bị bỏ quên, cần quyết định;
  - gợi ý "đơn tiếp theo". Với Specialist, hệ thống bỏ qua đơn HIGH và không gợi ý khi đã hết slot.

**Dashboard (chỉ Manager).** Nguồn: `S/domain/case_metrics.py:58-232`.

| Nhóm | Nội dung |
|---|---|
| Tổng quan | Số đơn theo trạng thái, quá hạn, leo thang, bị bỏ quên, cần quyết định; tỉ lệ đã đóng, tỉ lệ quá hạn, tỉ lệ HIGH |
| Phân bố rủi ro | Theo mức, theo dải điểm 0,2; xu hướng theo ngày |
| Điểm nóng | Top 10 người bán và top 10 danh mục, xếp theo số đơn HIGH |
| Khối lượng | Mỗi Specialist: đang xử lý / capacity / quá hạn |
| Hiệu quả CSKH | Đã liên lạc, liên lạc được, liên lạc lần đầu trong SLA, trung vị giờ tới lần liên lạc đầu, phát hiện vấn đề, vấn đề đã xử lý tiếp, đơn HIGH chưa liên lạc |
| Gợi ý hành động | `ASSIGN_HIGH` (gợi ý người còn nhiều slot nhất), `REBALANCE`, `STALE`, `DECIDE`, `SELLER_HOTSPOT` (≥ 3 đơn HIGH và ≥ 50% là HIGH; ngưỡng ghi cứng) |

---

## 8. Dữ liệu

### 8.1 Schema `ml`: kết quả mô hình (bất biến)

| Bảng / view | Nội dung chính |
|---|---|
| `model_releases` | Phiên bản mô hình, SHA-256 của artifact và dataset, `aggregation_rule='max-v1'`, `evaluation_status` ∈ {EXPLORATORY_NON_CONFIRMATORY, CONFIRMATORY, SYNTHETIC_DEMO} |
| `model_thresholds` | `medium_from` < `high_from`, cả hai trong [0,1]; chính sách chọn ngưỡng |
| `predictions` | Mỗi lần chấm điểm theo lô. `state`: READY → ACTIVE → SUPERSEDED, hoặc READY → REJECTED. **Toàn hệ thống chỉ có một ACTIVE**. Chỉ release CONFIRMATORY hoặc SYNTHETIC_DEMO được kích hoạt |
| `item_prediction_scores` | Điểm từng sản phẩm, `product_item_id = order_id-order_item_id`, top factors (JSON) |
| `order_prediction_scores` | Điểm đơn = điểm sản phẩm cao nhất (DB kiểm tra `score = top_item_score`); số sản phẩm; giá trị đơn |
| `v_risk_orders_for_web`, `v_risk_items_for_web` | Chỉ lấy prediction ACTIVE. `risk_level` được tính ngay trong view: HIGH nếu điểm ≥ `high_from`, MEDIUM nếu ≥ `medium_from`, còn lại LOW |
| `v_active_thresholds` | Ngưỡng của prediction đang ACTIVE |

Nguồn: `M/V001`, `M/V002`, `M/V016`, `M/V020`. Mọi bảng `ml.*` đều bị chặn UPDATE/DELETE, ngoại lệ duy nhất là chuyển `state` của prediction.

### 8.2 Schema `app`: nghiệp vụ

| Bảng | Nội dung | Ràng buộc chính |
|---|---|---|
| `users` | Tài khoản, vai trò, ngôn ngữ (`vi`/`en`), `is_active` | `username` UNIQUE |
| `review_cases` | Một case cho mỗi đơn: trạng thái, kết quả, lý do bỏ qua, người được giao, `cycle_no`, `reopen_count`, `row_version` | `order_id` UNIQUE; snapshot bị khóa |
| `review_cycles` | Mỗi lần vào hàng đợi: bắt đầu/kết thúc, hạn SLA, phiên bản tham số | Một chu kỳ mở cho mỗi case |
| `assignments` | Lịch sử giao đơn | Một lượt giao còn hiệu lực cho mỗi case |
| `contact_attempts` | Các lần liên lạc | Chỉ thêm |
| `contact_evidence`, `evidence_uploads` | Minh chứng (PNG/JPG/PDF ≤ 5 MB) | Đã gắn thì không sửa hay xóa được |
| `case_comments`, `manager_decisions` | Bình luận, quyết định | Chỉ thêm |
| `parameter_definitions`, `parameters`, `parameter_bundles` | Danh mục tham số, các phiên bản, nhóm phiên bản theo lần sửa | Chỉ thêm |
| `sla_adjustments` | Hạn SLA được tính lại khi tham số đổi | Chỉ thêm |
| `audit_events`, `audit_corrections` | Nhật ký kiểm toán; khi cần sửa thì thêm bản ghi đính chính, không sửa bản ghi gốc | Chỉ thêm |

Nguồn: `M/V003`–`M/V018`.

- **Phân quyền ở DB:** role `app_runtime` (backend) không đọc được bảng `ml` gốc mà chỉ đọc các view.

### 8.3 Schema `bronze`

`ingestion_runs` cùng 9 bảng thô, mọi cột ở dạng text và gắn `run_id`. Việc ép kiểu thực hiện ở dbt Silver (`M/V019`).

---

## 9. Tích hợp mô hình và tác vụ theo lô

| Bước | Hiện thực | Nguồn |
|---|---|---|
| Nạp dữ liệu | `build-bronze-manifest`, `ingest` (CLI) | `S/interfaces/cli.py` |
| Biến đổi | `make warehouse` → `dbt build` | `compose.yaml:91-105` |
| Huấn luyện | `train` (CLI); có các cờ cho lần chạy test niêm phong | `cli.py:46-98` |
| Chấm điểm | Kiểm tra SHA-256 của artifact và schema, `predict_proba`, `max-v1` (hòa điểm thì chọn `product_item_id` nhỏ nhất theo thứ tự chữ), ghi một prediction READY | `S/application/release_scoring.py:63-176` |
| Đưa vào hàng đợi | Lấy prediction ACTIVE; đưa **mọi mức kể cả LOW** vào; `ON CONFLICT (order_id) DO NOTHING` nên chạy lại không tạo trùng; tạo chu kỳ 1 và sự kiện `QUEUE_SEED` | `S/infrastructure/postgres_queue_seeding.py:16-69` |
| Tính lại SLA | `recalculate-sla` (CLI) | `sla_recalculation.py` |
| Dọn minh chứng | `purge-evidence --retention-hours 24` (CLI) | `evidence_cleanup.py` |

**Khoảng trống:** chấm điểm và đưa vào hàng đợi chưa có lệnh CLI. `make score` chỉ chạy một lệnh do người dùng tự cung cấp.

**Sự kiện kiểm toán** (`S/infrastructure/postgres_*`):

| Loại | Ý nghĩa |
|---|---|
| `QUEUE_SEED` | Đơn được đưa vào hàng đợi |
| `CLAIM` | Specialist tự nhận đơn |
| `ASSIGN`, `REASSIGN` | Manager giao hoặc chuyển đơn |
| `OVERRIDE` | Giao vượt `capacity` |
| `STATUS` | Hoàn tất đơn |
| `SKIP` | Bỏ qua đơn, kể cả khi hệ thống tự bỏ qua |
| `REOPEN` | Mở lại đơn |
| `COMMENT`, `MODEL_NOTE` | Bình luận, ghi chú mô hình |
| `CONTACT` | Ghi một lần liên lạc |
| `DECISION` | Quyết định của Manager |
| `PARAMETER_CHANGE` | Thay đổi tham số |

**Xác thực.** JWT HS256, hết hạn sau 30 phút, không có refresh token; logout không xử lý gì ở server. Mật khẩu băm Argon2. Tài khoản bị vô hiệu hóa thì token cũ cũng mất hiệu lực (`S/application/auth.py:25-53`).

---

## 10. Khác biệt so với tài liệu cũ trong `docs/`

| # | Tài liệu cũ nói | Code hiện tại |
|---|---|---|
| 1 | Hàng đợi chứa đơn có rủi ro (MEDIUM/HIGH) | Đưa **mọi mức, kể cả LOW**, vào hàng đợi |
| 2 | Lịch SLA cấu hình được (BUSINESS_HOURS) | Tham số có nhưng **chưa dùng**; luôn tính theo giờ đồng hồ |
| 3 | `first_touch_hours`, `retry_gap_days`, `capacity_warn` là luật vận hành | Chỉ hiển thị, **không được áp dụng** |
| 4 | Kênh liên lạc PHONE/EMAIL/CHAT/OTHER (Data Dictionary) | API nhận PHONE/EMAIL/MESSAGE; `OTHER` không dùng được |
| 5 | Giao diện song ngữ (FRD F11) | Nhãn giao diện ghi cứng tiếng Anh; chỉ thông báo lỗi từ backend được dịch |
| 6 | Trang Decisions là một mục trong điều hướng | Route có, nhưng **không có link** trong thanh điều hướng |
| 7 | ERD P7 chỉ có 6 bảng | Có 15 bảng trong `app` (V006–V018 bổ sung) |
| 8 | Web hiển thị kết quả mô hình | Hiện là **dữ liệu demo tổng hợp**; mô hình EXPLORATORY bị DB chặn kích hoạt |
| 9 | Có lệnh chấm điểm / đưa vào hàng đợi | Có mã nhưng **chưa có CLI** gọi tới |
| 10 | Khoảng tham số theo DB (ví dụ capacity ≤ 1000) | Ứng dụng giới hạn chặt hơn (capacity 1–20, max_contact 1–10) |
| 11 | Quyết định của Manager dành cho đơn đã đóng | Ghi được ở **mọi trạng thái**; "cần quyết định" = đơn đã đóng mà chưa có quyết định |

---

## 11. Nhật ký kiểm tra

Tài liệu được dựng từ ba lượt đọc code độc lập (migrations; backend/domain/API; frontend + tác vụ ML), sau đó kiểm tra đối chiếu hai vòng trực tiếp trên mã nguồn.

| Vòng | Điểm kiểm tra | Kết quả |
|---|---|---|
| 1 | Seed đưa mọi mức (kể cả LOW) vào hàng đợi | Đúng: `postgres_queue_seeding.py` chỉ lọc `state='ACTIVE'` |
| 1 | `sla_calendar` không được dùng khi tính hạn | Đúng: chỉ xuất hiện khi đọc cấu hình (`postgres_operational_reads.py:46`) |
| 1 | `first_touch_hours`, `retry_gap_days`, `capacity_warn` không được áp dụng | Đúng: backend chỉ có ở `parameters.py` và phần đọc cấu hình |
| 1 | Tối đa 3 tệp minh chứng, 5 MB | Đúng: `domain/workflow.py:101-102` |
| 1 | JWT 30 phút | Đúng: `api/config.py:10` |
| 1 | Không có link `/decisions` trong thanh điều hướng | Đúng: `app-shell.component.ts:8-14` |
| 1 | Số bảng trong `app` | **Sai, đã sửa** 16 → 15 |
| 1 | Khoảng `reopen_review_*` | Đúng: 1–60 ngày / 1–10 lần |
| 2 | Danh sách 15 bảng `app` khớp mục 8.2 | Đúng |
| 2 | Frontend có áp dụng 3 tham số chưa dùng không | Không: chỉ có ở màn tham số và DTO (kiểm tra chéo `capacity_warn < capacity`) |
| 2 | Giao diện có thư viện dịch (i18n) không | Không tìm thấy; nhãn ghi cứng tiếng Anh |
| 2 | Quyết định không đổi trạng thái | Đúng: `postgres_workflow_commands.py:485` |
| 2 | Tập giá trị `outcome`, `skip_reason`, OTHER cần ghi chú | Đúng: `domain/workflow.py:21-22,66-67` |

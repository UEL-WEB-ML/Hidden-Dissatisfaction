# Project history

Tài liệu này cung cấp toàn cảnh những phần việc đã được thực hiện trong repository, dựa trên lịch
sử Git. Đây không phải bảng chấm công và không dùng số commit để đánh giá mức độ đóng góp.

**Phạm vi:** nhánh `dev` đến commit `446e283`, cập nhật ngày 2026-10-12. Các merge commit được ghi
nhận như mốc tích hợp, không tính thành một phần việc độc lập.

## Thành viên và định danh Git

| Thành viên/định danh | Alias xuất hiện trong Git | Mảng đóng góp chính |
|---|---|---|
| Quan | `Quan` | EDA, phân tích bài toán, xây dựng và kiểm tra modelling dataset |
| Truc | `Truc`, `TrucVu` | Web prototype, wireframe, sơ đồ luồng, API contract và tích hợp giao diện |
| Nguyen T. Thuy / Huy | `nguyentthuy11work-dev`, `huytensordaily` | Kiến trúc dự án, research/data contract, domain rules, CI và tích hợp nhánh dữ liệu |

Hai alias có cùng email Git được gom thành một thành viên. Nếu cách ánh xạ trên chưa đúng, thành
viên liên quan nên sửa bảng này bằng pull request.

## Lịch sử theo thời gian

### 2026-09-24 — EDA và xác định khoảng trống nghiên cứu

**Quan**

- Thực hiện EDA tổng quát và EDA cho bài toán kinh doanh trên dữ liệu Olist.
- Xây dựng notebook phân tích vì sao lateness thường chi phối mô hình và làm rõ nhóm đơn giao đúng
  hạn nhưng vẫn nhận đánh giá thấp.
- Tạo bộ hình EDA về coverage, nhịp đặt hàng, vận hành theo thời gian, nhóm sản phẩm, thanh toán,
  địa lý, review và tương quan.

Commit tiêu biểu: `055bed5`.

### 2026-09-30 — Web wireframe đầu tiên

**Truc**

- Xây dựng HTML wireframe gồm danh sách/risk queue, chi tiết đơn hàng, action view và data-quality
  view.
- Thêm style, JavaScript dùng chung và mock data phục vụ demo giao diện.
- Tích hợp qua pull request #1.

Commit tiêu biểu: `e799e11`, merge `18bb10c`.

### 2026-10-01 — Figma, đăng nhập và phân quyền giao diện

**Truc**

- Gắn liên kết Figma vào wireframe và tài liệu hướng dẫn.
- Thêm màn hình login, overview và các góc nhìn theo vai trò.
- Loại bỏ Data Quality khỏi phạm vi giao diện tại thời điểm đó.
- Tích hợp qua pull request #2 và #3.

Commit tiêu biểu: `7b53e37`, `4f3cb90`; merge `57aa6a5`, `6e6100d`.

### 2026-10-05 — Chuẩn hóa nền tảng nghiên cứu và cấu trúc repository

**Nguyen T. Thuy / Huy**

- Định nghĩa research design: cohort, prediction time, target, feature được phép/cấm, temporal
  validation và các chỉ số bắt buộc.
- Viết problem statement, literature review, data contract và kiến trúc phân lớp.
- Tạo package Python theo các lớp domain/application/infrastructure/interfaces.
- Cài đặt domain rule cho primary cohort, CLI ban đầu và unit tests.
- Thiết lập `pyproject.toml`, pre-commit, GitHub Actions, cấu trúc data/artifact/report và hướng dẫn
  đóng góp.
- Loại bỏ `AGENTS.md` khỏi repository sau khi cấu trúc ban đầu được tạo.

Commit tiêu biểu: `a98f9bd`, `a3f9f82`.

### 2026-10-05 — Cập nhật prototype theo BRD/FRD và hợp đồng API

**Truc**

- Tạo use-case và user-flow cho manager và specialist.
- Cập nhật prototype theo BRD v3.0 và FRD v1.0; thêm Audit History và bỏ Action Tracking.
- Tổ chức lại `Wireframe` thành `Prototype`, tách HTML/CSS/JavaScript.
- Viết bản nháp API contract và web data dictionary.
- Thêm lớp `api.js` và mock server; chuyển giao diện sang sử dụng API abstraction.
- Cập nhật README, trạng thái Figma và hợp nhất các thay đổi giao diện vào `main`.

Commit tiêu biểu: `f9bee36`, `6caea58`, `91f2649`, `7614d47`, `34e40a4`; merge `fd820f1`,
`86aff0e`, `8a0dec4`.

### 2026-10-12 — Modelling dataset và kiểm tra chất lượng dữ liệu

**Quan**

- Bổ sung notebook xây dựng modelling dataset ở grain một dòng trên mỗi order.
- Thêm kiểm tra join, dữ liệu thời gian bất hợp lệ, point-in-time seller history, missingness, label
  uncertainty và temporal split.
- Tạo data dictionary và đầu ra Parquet phục vụ modeling.
- Bổ sung metadata dataset và cập nhật notebook EDA hiện có.

Commit tiêu biểu: `2104015`.

### 2026-10-12 — Tích hợp EDA/pre-modeling và sửa cấu hình dự án

**Nguyen T. Thuy / Huy**

- Đồng bộ `dev` vào nhánh `feat/EDA&pre-modeling` và tích hợp pull request #7 vào `dev`.
- Sửa conflict ngữ nghĩa trong `pyproject.toml`: loại bỏ khai báo `[project]` trùng khiến CI không
  thể parse/cài package.
- Xác nhận lại quality workflow sau bản sửa.

Commit tiêu biểu: `3421cdf`, merge `40c7f1e`, fix `e997d35`.

### 2026-10-12 — Chuẩn hóa môi trường phát triển bằng uv

**Nguyen T. Thuy / Huy**

- Thống nhất Python 3.11 giữa môi trường local và CI.
- Tạo và commit `uv.lock` để các thành viên sử dụng cùng phiên bản dependency.
- Chuyển hướng dẫn cài đặt, chạy notebook và quality gates sang `uv sync --frozen` và `uv run`.
- Chuyển GitHub Actions từ cài package bằng pip sang `astral-sh/setup-uv` và lockfile.

Commit tiêu biểu: `446e283`.

## Công việc đang ở nhánh riêng, chưa thuộc `dev`

Phần này giúp nhóm thấy việc đang chờ review nhưng không được hiểu là đã tích hợp.

| Nhánh | Người thực hiện | Nội dung | Commit |
|---|---|---|---|
| `feat/modeling-training-pipeline` | Nguyen T. Thuy / Huy | Temporal modeling/training pipeline, leakage guard, calibration, budget evaluation, CLI, notebook và tests | `a8f628c` |

Khi nhánh được merge, hãy chuyển nội dung tương ứng vào lịch sử theo thời gian và cập nhật commit
phạm vi ở đầu tài liệu.

## Checkpoint local chưa commit — 2026-10-28

Phần này là checkpoint để tiếp tục phiên làm việc, không phải lịch sử đã merge và không gán đóng
góp cho thành viên cho đến khi thay đổi được review/commit.

### Môi trường và dữ liệu

- PostgreSQL/Flyway đã được khởi tạo; migrations V001–V019 đã chạy thành công.
- Bronze source run: `6f13bf55-5ce3-4a58-807e-e1c31ff76eaa`.
- dbt build mặc định loại `tag:release_only`; lần rebuild gần nhất pass 85/85 resources.
- Dataset `data/processed/modelling_items.parquet` có 97.884 item thuộc 85.425 order và dùng feature
  schema `p5-item-v2-delivery-product`. Parquet, manifest và model checkpoints là local/ignored.

### Modeling development-only đã thực hiện

- Protocol v2 bổ sung CatBoost GPU nhưng không mở sealed final test. Development winner khi đó là
  `order_reference:catboost-gpu-depth8-v1`, PR-AUC dao động quanh 0,199–0,204 giữa các GPU run.
- Protocol v3 thử CatBoost native categorical; candidate mới không cải thiện và winner vẫn là
  CatBoost ordinal cũ.
- Protocol v4 bổ sung feature hợp lệ tại `prediction_at`: ETA buffer, purchase/carrier-to-delivery
  duration, order size/value concentration và physical product attributes.
- V4 development winner là `order_weight:random_forest-depth8-leaf5-v1`, holdout order PR-AUC
  `0.210955`, Brier `0.205759`, calibration `sigmoid`. Đây là cải thiện so với v3 nhưng chưa đạt
  stop gate PR-AUC 0,25.
- Strategy 1 (ADR-014) đã thêm challenger `order_aggregate`. Aggregation thật cho kết quả đúng một
  row/order, không duplicate, order weight bằng 1 và category-set có thứ tự ổn định.
- CPU precheck v5: order-level tốt nhất là
  `order_aggregate:random_forest-depth12-leaf10-v1`, PR-AUC `0.202278`, Brier `0.190912`; chưa thắng
  v4 item/order-weight winner `0.210955`.
- Ruff, Black, Mypy và 11 schema/aggregation/training tests pass. Sealed final test chưa chạy.

### Accuracy plan S1–S10 — 2026-10-29

- Hoàn thành các ablation S1–S10 trên temporal development partitions và giữ seller operations,
  order composition, product morphology/content trong feature set cuối.
- Retained Random Forest đạt rolling order PR-AUC `0.146502`, tăng `0.010176` so với baseline
  `0.136326`; bounded CatBoost GPU depth 6 đạt holdout `0.223873` nhưng rolling PR-AUC thấp hơn ở
  `0.145813`, nên không thay winner theo metric chính.
- Accuracy plan đóng theo nhánh dừng có chủ đích vì chưa đạt target `0.25`. Historical final-test
  không được mở lại; P12 tiếp tục block confirmatory claim khi chưa có replacement holdout.

### Sửa pipeline đáng chú ý

- Regime transformation nay được áp dụng nhất quán cho fit, rolling validation, selection,
  calibration và threshold; trước đó một số bước vẫn dùng item rows dù fit theo reference regime.
- `TrainingConfig.from_toml` nay đọc danh sách `models.regimes` thay vì âm thầm dùng default.
- ADR-011 đến ADR-014 ghi lại GPU candidate, native categorical tuning, feature schema v2 và
  order-level challenger.

### Blocker và cách tiếp tục

- Official v5 comparison có CatBoost GPU **chưa chạy xong**. Ubuntu WSL interop đang lỗi
  `UtilAcceptVsock:273: accept4 failed 110`; shell hiện tại không thấy GPU và CatBoost local lỗi
  `CUDA error 35: CUDA driver version is insufficient for CUDA runtime version`.
- Không có process `hidden-dissatisfaction train` hoặc CatBoost trong process namespace hiện tại;
  GPU có thể thuộc một WSL/session khác. Không kill rộng hoặc chạy `wsl --shutdown` trước khi kiểm
  tra session đó có kết quả cần giữ hay không.
- Sau khi WSL/GPU phục hồi, chạy từ Windows/Ubuntu:

```bash
wsl -d Ubuntu -- bash -lc 'nvidia-smi'
wsl -d Ubuntu -- bash -lc 'cd /home/hatca/projects/Hidden-Dissatisfaction && .venv/bin/hidden-dissatisfaction train --data data/processed/modelling_items.parquet --config configs/experiment.toml --output-root . --selection-record artifacts/checkpoints/p5-v5-order-aggregate-selection.json > /tmp/hidden-dissatisfaction-p5-v5-report.json'
```

- Sau run, so sánh `selection_holdout_order_pr_auc` của mọi key `order_aggregate:*` với winner v4
  `0.210955`. Chỉ freeze selection mới nếu improvement ổn định; tuyệt đối không dùng
  `--finalize-test` ở bước này.

## Quy ước cập nhật HISTORY

1. Cập nhật file trong cùng pull request với phần việc cần ghi nhận.
2. Mô tả kết quả hoặc quyết định có thể kiểm chứng; không ghi nhận kế hoạch như việc đã hoàn thành.
3. Ghi tên thành viên và ít nhất một commit hoặc pull request tiêu biểu.
4. Phân biệt rõ việc đã merge vào `dev` với việc còn nằm trên feature branch.
5. Không dùng số commit, số dòng hoặc thứ tự tên để suy ra mức độ đóng góp.
6. Nếu sửa lại hoặc loại bỏ một phần việc cũ, thêm mốc mới thay vì xóa lịch sử trước đó.

## Cách kiểm chứng

```bash
git log dev --date=short --format="%h %ad %an %s" --reverse
git shortlog -sne dev
git show --stat <commit>
```

Lịch sử này được biên soạn từ commit metadata và nội dung thay đổi. Những đóng góp ngoài Git như
họp, nghiên cứu, thiết kế trên công cụ bên ngoài hoặc chuẩn bị dữ liệu chưa commit sẽ không tự động
xuất hiện và cần được thành viên bổ sung kèm nguồn tham chiếu phù hợp.

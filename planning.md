# Hidden Dissatisfaction — Implementation Plan

## 1. Mục đích và phạm vi

Tài liệu này là kế hoạch thực thi để hoàn thiện toàn bộ hệ thống Hidden Dissatisfaction từ dữ liệu Olist đến luận văn và demo. Kế hoạch áp dụng các nguyên tắc của project template `TinyBigCorp` nhưng giữ nguyên các contract và cấu trúc đang có của repository này.

Phạm vi gồm:

- PostgreSQL Medallion Warehouse: Bronze, Silver, Gold.
- dbt transformations, tests, documentation và lineage.
- Product-item modeling dataset và ML training/evaluation.
- ML release, prediction persistence và order aggregation `max-v1`.
- Backend FastAPI theo Clean Architecture.
- Frontend Angular theo MVVM + Signals.
- Workflow CSKH F01–F12 theo BRD/FRD/API Contract.
- Docker Compose, CI, contract tests, E2E tests.
- Báo cáo thực nghiệm, luận văn và demo.

Ngoài phạm vi:

- Không dùng `ds_with_ai_capstone`, code, metric hoặc kết quả của repository đó.
- Không phát triển tiếp trong `ML_docs` hoặc `Docker_Environment`; hai repository này chỉ là backup.
- Không xây cơ chế tự động liên hệ, hoàn tiền, voucher hoặc suy luận nhân quả.
- Không biến prototype HTML hiện có thành production frontend bằng cách mở rộng tùy tiện; prototype chỉ là tài liệu tham chiếu hành vi/UI.

## 2. Nguồn sự thật và thứ tự ưu tiên

Khi tài liệu hoặc implementation mâu thuẫn, dùng thứ tự sau:

1. PostgreSQL migrations/schema runtime và implementation đã kiểm thử.
2. `BA/` — bộ tài liệu as-built.
3. `docs/research-design.md` và `docs/data-contract.md`.
4. `docs/architecture.md` và tài liệu triển khai khác.
5. Prototype/mock lịch sử.

Mọi thay đổi contract phải sửa tài liệu có version trong cùng pull request trước hoặc cùng lúc với code. Không sửa code để “khớp mock” nếu mock trái contract.

## 3. Các quyết định đã cố định

- Repository duy nhất: `Hidden-Dissatisfaction`.
- ML grain: một product item, khóa ổn định `product_item_id = order_id + '-' + order_item_id`.
- Workflow, temporal split, bootstrap và prioritization grain: order.
- Các item cùng order kế thừa cùng observed review label; đây là weak label, không phải causal attribution.
- Population chính: order đã giao đúng hạn hoặc sớm, có review quan sát được.
- Target: `negative = 1` khi review score thuộc `{1, 2}`.
- Prediction time: ngay sau xác nhận giao hàng, trước mọi review information.
- Order aggregation đầu tiên: `max-v1`.
- Canonical raw path: `data/raw/olist/`.
- Canonical processed artifact: `data/processed/modelling_items.parquet` kèm manifest.
- Database: `hidden_dissatisfaction`.
- Schema: `bronze`, `silver`, `gold`, `ml`, `app`.
- Attempt, Comment, Decision và Audit là append-only theo contract.
- Evidence chỉ nhận PNG/JPG/PDF, tối đa 3 file/Attempt, tối đa 5 MB/file.
- Attempt không thành công cuối cùng tự chuyển `SKIPPED/UNREACHABLE` trong cùng transaction.
- Manager Decision bắt buộc `decision`, `reason`, `next_step`.

## 4. Quy tắc kiến trúc kế thừa từ template

### 4.1. Backend: Clean Architecture

Dependency chỉ được hướng vào trong:

```text
HTTP/CLI -> Application -> Domain
              ^             ^
              |             |
        Infrastructure implements ports
```

| Layer          | Được sở hữu                                                                        | Không được sở hữu                            |
| -------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Domain         | Entity, value object, enum, state transition, policy thuần, repository/service port    | FastAPI, SQLAlchemy, pandas, dbt, filesystem, HTTP |
| Application    | Command/query DTO, use case, transaction orchestration, authorization policy invocation | SQL trực tiếp, framework response, UI logic      |
| Infrastructure | SQLAlchemy/PostgreSQL repository, auth, clock, file storage, dbt/ML adapter             | Business rule mới hoặc HTTP status mapping       |
| Interfaces     | FastAPI router, dependency wiring, CLI, request/response mapping                        | State transition, SQL, feature engineering         |

Quy tắc bắt buộc:

- Domain và application phụ thuộc abstraction/port, không khởi tạo concrete repository.
- FastAPI route phải mỏng: parse, authorize qua dependency/use case, gọi use case, map response/error.
- Pydantic model kiểm tra dữ liệu ở boundary; domain vẫn bảo vệ invariant của chính nó.
- Một transaction boundary cho mỗi write use case.
- Clock, UUID generator, password hasher, token service và file storage đều có interface để test thay thế được.
- Pure transformation dùng function; class chỉ dùng khi cần state, lifecycle, polymorphism hoặc dependency injection.
- Interface nhỏ theo use case/read model; không tạo một “god repository”.

### 4.2. Frontend: MVVM + Signals

```text
Template/View -> Component/ViewModel (signals) -> Facade/Store -> API service -> Backend
```

Quy tắc bắt buộc:

- Standalone Angular components và lazy feature routes.
- Component giữ presentation state bằng Signals; không gọi `fetch`/HttpClient trực tiếp.
- API DTO tách khỏi ViewModel; mapper là pure function.
- Shared state đặt trong feature facade/store, không đặt trong service singleton tùy tiện.
- Dùng Reactive Forms cho mọi write form.
- Auth và language header qua interceptor; role/state qua route guard và action policy.
- Frontend ẩn/disable action sai quyền để UX rõ, nhưng Backend vẫn là nơi thực thi business rule.
- Mọi trang có loading, empty, validation, forbidden, conflict và server-error state.

### 4.3. Migration-first và contract-first

Thứ tự của một vertical slice có persistence/API/UI:

1. Xác nhận acceptance criteria và API contract.
2. Tạo migration forward-only.
3. Tạo/điều chỉnh domain model và port.
4. Viết application command/query và use case.
5. Viết infrastructure adapter/repository.
6. Viết HTTP DTO/router/error mapping.
7. Viết frontend model/API/facade/view.
8. Viết unit, integration, contract và E2E tests.
9. Cập nhật docs, OpenAPI example và traceability.

Không bắt đầu bằng route hoặc UI rồi mới bổ sung business rule sau.

### 4.4. Testing pyramid

- Nhiều unit tests: domain policy, application use case, mapper, Signal store/component.
- Đủ integration tests: PostgreSQL repository, migrations, dbt, file storage, API.
- Contract tests: mọi endpoint và error envelope của API 0.5.
- Ít nhưng đầy đủ E2E tests: critical workflow của Specialist và Manager.
- Không dùng database thật cho domain unit tests; dùng fake/in-memory port.
- Domain/Application đạt 100% line coverage theo yêu cầu template; phần còn lại dùng threshold được đo và nâng dần, không dùng coverage thay cho scenario correctness.

### 4.5. Coding rules và architecture fitness tests

- Python: class `PascalCase`, function/variable `snake_case`, private member `_prefix`, constant/config key `UPPER_CASE`; Ruff, Black, Mypy strict và double quotes.
- TypeScript: file `kebab-case`, class `PascalCase`, Observable có hậu tố `$`, Signal dùng noun phrase; ESLint, Prettier, single quotes và 2-space indentation.
- SQL: table `snake_case` số nhiều, constraint/index có tên rõ; SQL keyword viết hoa trong migration mới.
- Mọi public Python method có docstring; public TypeScript API có JSDoc khi behavior/contract không hiển nhiên.
- Mỗi repository có ABC/Protocol riêng; database exception phải được map sang domain/application exception trước router.
- Không expose SQLAlchemy model ra API; luôn map sang domain/read model rồi Pydantic response DTO.
- Không global mutable state; không schema change thủ công ngoài Flyway migration.
- Frontend tạo `src/app/theme/colors.ts`, `typography.scss`, `icons.registry.ts` và CSS variables trước feature styling.
- Dùng smart/container và dumb/presentational components; derived state dùng `computed`; side effect có chủ đích dùng `effect`.
- Không đặt filter/map/business expression trong HTML template, không dùng `any`, không hard-code màu trong component SCSS và không dùng `app.module`.

Ba fitness tests ở mỗi release:

1. **Swap test:** thay PostgreSQL/file storage/mock model adapter chỉ cần đổi Infrastructure + DI.
2. **Junior test:** đọc Domain hiểu state/policy mà không cần SQL/HTTP.
3. **Reskin test:** đổi theme bằng design tokens, không sửa từng feature component.

## 5. Kiến trúc thư mục mục tiêu

Không di chuyển code ML hiện có chỉ để giống tên thư mục template. Áp dụng pattern của template vào package hiện tại để tránh churn không cần thiết.

```text
Hidden-Dissatisfaction/
├── configs/
├── data/
├── dbt/
├── frontend/
├── infra/
│   ├── postgres/
│   │   ├── init/
│   │   └── migrations/
│   └── evidence/
├── notebooks/
├── reports/
├── scripts/
├── src/hidden_dissatisfaction/
│   ├── domain/
│   │   ├── entities/
│   │   ├── policies/
│   │   ├── repositories/
│   │   └── services/
│   ├── application/
│   │   ├── commands/
│   │   ├── queries/
│   │   ├── dtos/
│   │   ├── ports/
│   │   └── use_cases/
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── repositories/
│   │   ├── auth/
│   │   ├── storage/
│   │   └── ml/
│   ├── interfaces/
│   │   ├── http/
│   │   └── cli.py
│   └── modeling/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── acceptance/
│   └── fixtures/
├── web/
│   ├── Prototype/
│   ├── Wireframe/
│   ├── SoDo/
│   └── BaoCao_LaTeX/
├── compose.yaml
├── planning.md
├── pyproject.toml
└── uv.lock
```

`frontend/prototype` là đường dẫn frontend tĩnh đã bàn giao. `web/Wireframe` chỉ là tài liệu tham khảo
đã lưu trữ, không phải đường dẫn ứng dụng đang hoạt động.

## 6. Definition of Ready và Definition of Done

### Definition of Ready cho một feature

- Có mã BRD/FRD tương ứng.
- Input/output/error đã rõ trong API Contract hoặc được version hóa trước khi code.
- Data ownership, transaction boundary và quyền actor đã rõ.
- Không còn decision gate chặn feature.
- Có acceptance scenarios gồm happy path, validation, permission và concurrency khi liên quan.

### Definition of Done cho một feature

- Migration/model/domain/use case/adapter/API/UI cần thiết đã hoàn thành.
- Không có business rule trong route, SQL view hoặc Angular template mà domain/application không kiểm soát.
- Unit, integration, contract và E2E test phù hợp đều đạt.
- Ruff, Black, Mypy, Pytest, ESLint, Prettier, Vitest và production build đạt.
- OpenAPI/API checker đạt với response/error thật.
- Role, append-only, audit, timezone và concurrency được kiểm tra.
- Không làm thay đổi model output từ web workflow.
- Docs và traceability được cập nhật.
- Có bằng chứng chạy được từ clean checkout.

## 7. Dependency map và thứ tự bắt buộc

```text
P0 decisions + repository baseline
  -> P1 platform/CI/Compose
  -> P2 Bronze
  -> P3 dbt Silver/Gold
  -> P4 product-item mart
  -> P5 ML training/evaluation
  -> P6 ML release/views
  -> P7 app ERD/migrations
  -> P8 backend foundation
  -> P9 backend workflow features
  -> P10 Angular foundation/features
  -> P11 E2E hardening
  -> P12 thesis/demo/release
```

Frontend foundation có thể bắt đầu sau P0 bằng mock API 0.5, nhưng frontend integration chỉ được đóng sau backend contract tests. Backend app migration có thể chạy song song với P4–P5 sau khi ERD đã chốt; `review_cases.prediction_id` chỉ được bật FK khi P6 đã tạo bảng ML chính thức.

---

## 8. Kế hoạch thực thi chi tiết

### P0 — Baseline, tích hợp branch và decision gates

#### P0.1 — Đóng gói snapshot consolidation hiện tại

**Mục tiêu:** tạo điểm khôi phục sạch trước khi nhập code từ `origin/main`.

Các bước:

1. Review toàn bộ modified/untracked files, đặc biệt docs, `compose.yaml`, `infra/`, report và diagrams.
2. Chạy lại quality gate hiện tại và `git diff --check`.
3. Commit snapshot consolidation riêng, không trộn với dbt/prototype import.
4. Merge/rebase theo workflow nhóm sau khi working tree sạch; không merge nguyên `origin/main` vào tree bẩn.
5. Ghi commit SHA baseline vào `docs/consolidation-manifest.md`.

**DoD:** working tree sạch; snapshot có commit; 14+ test hiện tại và quality gates đạt.

#### P0.2 — Nhập có chọn lọc phần hợp lệ từ `origin/main`

Nhập snapshot, không tái tạo lịch sử source repository:

- `dbt/`.
- `scripts/load_bronze.py`.
- `scripts/build_silver.py` để refactor, không giữ path cũ.
- `sql/migrations/001_bronze.sql` vào migration sequence mới.
- `frontend/prototype/` là frontend đã bàn giao; `web/Wireframe/` chỉ là reference/archive.

Không ghi đè tài liệu 4.2/2.2/0.5 hiện hành bằng bản cũ trên `origin/main`. Không giữ mặc định `ironman`, path `../Docker_Environment` hoặc env ngoài repository.

**DoD:** import là một commit độc lập; diff chỉ có snapshot cần thiết; không thay đổi backup repositories.

#### P0.3 — Chốt các decision gate còn mở

Tạo `docs/adr/` và mỗi quyết định dưới đây có một ADR với Context, Decision, Alternatives, Consequences:

| ADR     | Quyết định cần chốt         | Đề xuất mặc định để review                                                              | Chặn            |
| ------- | -------------------------------- | ----------------------------------------------------------------------------------------------- | ---------------- |
| ADR-001 | Multiple-review policy           | latest answered review, tie-break deterministic, flags cho sensitivity                          | Gold mart, label |
| ADR-002 | Timezone/API datetime            | DB UTC `timestamptz`, API ISO 8601 offset, UI localize; giữ timezone nguồn trong manifest   | SLA/API/UI       |
| ADR-003 | Authentication                   | JWT Bearer ngắn hạn cho MVP; password Argon2; không self-registration                        | Auth/frontend    |
| ADR-004 | SLA calendar                     | `CALENDAR` cho MVP; `BUSINESS_HOURS` chỉ bật khi có work schedule/holiday table          | SLA/parameters   |
| ADR-005 | Decision/outcome/skip catalogues | PO duyệt danh mục API 0.5 hoặc version contract                                              | DB/API/forms     |
| ADR-006 | Evidence storage/retention       | local volume adapter cho dev, object-storage port; retention do PO duyệt                       | Upload/audit     |
| ADR-007 | Mutable parameters               | chốt các key `in_brd=false` có cho Manager sửa hay read-only                              | F10              |
| ADR-008 | Same-time delivery/review        | rule intervention-window/sensitivity                                                            | Research cohort  |
| ADR-009 | Synthetic item policy            | Không tạo synthetic item trong production nếu raw item có đủ; fixture/demo phải gắn cờ | ML/API/UI        |

**DoD:** mọi ADR `Accepted`; cập nhật API/Data Dictionary nếu quyết định thay contract; không còn mục “TBD” chặn ERD.

#### P0.4 — Lập traceability matrix

Tạo `docs/traceability.md` với cột:

```text
BRD rule -> FRD function/sub-function -> API endpoint -> DB object
-> Backend use case -> Frontend route/component -> Test ID -> Status
```

**DoD:** F01–F12 và toàn bộ business rule BRD mục 6 có ít nhất một test target.

### P1 — Platform foundation, quality và CI

#### P1.1 — Chuẩn hóa dependency groups

1. Giữ dependency ML trong extra `ml`.
2. Thêm extra `warehouse`: `dbt-core`, `dbt-postgres`, PostgreSQL driver cần cho loader.
3. Thêm extra `api`: FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy asyncio, asyncpg, JWT/auth hash, multipart và structured logging.
4. Thêm dev dependencies: pytest-asyncio, httpx, testcontainers hoặc PostgreSQL test fixture.
5. Pin compatible ranges và cập nhật `uv.lock`.
6. Không đưa notebook/dbt/build tool vào runtime API image.

**Tests:** `uv sync --frozen` cho từng group; import smoke test.

#### P1.2 — Migration runner và database bootstrap

1. Giữ `infra/postgres/init/` chỉ cho role/schema/default privilege cần lúc volume mới.
2. Tạo versioned forward-only SQL ở `infra/postgres/migrations/`.
3. Thêm Flyway service/job vào Compose theo migration-first rule của template.
4. Baseline migration phải an toàn trên database mới; không chỉnh migration đã phát hành.
5. Thêm lệnh `make migrate`, `make migrate-info`, `make db-reset` với cảnh báo destructive rõ ràng.

**DoD:** database trống có thể `up -> migrate`; migration chạy lần hai không tạo thay đổi; schema history truy vấn được.

#### P1.3 — Mở rộng CI theo monorepo

Tạo các job độc lập:

- `python-quality`: Ruff, Black, Mypy.
- `python-unit`: unit tests không cần DB.
- `postgres-integration`: Postgres service, migration, repository/API tests.
- `dbt`: `dbt deps/parse/build` trên fixture Bronze nhỏ.
- `frontend-quality`: `npm ci`, ESLint, Prettier check, Vitest coverage.
- `frontend-build`: Angular production build.
- `compose-smoke`: build images, healthcheck, read-only endpoint.
- `docs-contract`: version assertions, Markdown links, OpenAPI/API 0.5 checker.

Chỉ upload artifact không có secret/raw data. Đặt coverage threshold sau khi baseline được đo; không hạ threshold để merge.

#### P1.4 — Secrets, logging và health endpoints

1. Mở rộng `.env.example` bằng placeholder, không commit credential.
2. Tách dev/test env; database test riêng.
3. Structured JSON logging có request/correlation ID, không log password/token/file content.
4. Thêm `/health/live` và `/health/ready`; readiness kiểm DB/migration version, không chạy query nặng.
5. Tạo `docs/local-development.md` runbook cho clean checkout.

**DoD P1:** CI chạy tự động; Compose khởi tạo DB/migration; Python và frontend build reproducibly.

### P2 — Bronze ingestion

#### P2.1 — Chuẩn hóa migration Bronze

1. Chuyển logic `001_bronze.sql` thành migration versioned theo sequence mới.
2. Tạo `bronze.ingestion_runs` và chín raw tables.
3. Mỗi row gắn `source_run_id`; constraint/index phục vụ dbt source filtering.
4. Không áp business transformation trong Bronze.
5. Quyền: loader chỉ INSERT/SELECT cần thiết; không có quyền vào `app`.

#### P2.2 — Refactor loader thành adapter có test

1. Tách manifest validation/checksum thành pure functions.
2. Tạo application use case `LoadBronzeRun` và database/file ports.
3. Adapter đọc đúng `data/raw/olist/`; không gọi Compose từ business code.
4. Validate đủ chín file, exact header, encoding, checksum và duplicate manifest entry.
5. Dùng advisory lock; run chuyển `STARTED -> COMPLETE/FAILED` rõ ràng.
6. COPY/load trong transaction phù hợp; failed run không được xem là source hợp lệ.
7. CLI `hidden-dissatisfaction ingest --manifest ...` hoặc script mỏng gọi use case.

#### P2.3 — Tests và evidence

- Unit: manifest, missing file, checksum mismatch, deterministic run metadata.
- Integration: load fixture chín file; rerun tạo historical run mới; concurrent lock; rollback/error status.
- Security: path traversal và CSV bất thường không ghi ngoài schema.

**DoD P2:** clean database nhận một completed ingestion run, row counts/checksums khớp manifest, không sửa raw files.

### P3 — dbt Silver/Gold core

#### P3.1 — Chuẩn hóa dbt project cho monorepo

1. Đổi mọi default database từ `ironman` sang `hidden_dissatisfaction`.
2. Xóa path/env phụ thuộc `Docker_Environment`.
3. Profile chỉ đọc env; không có secret thật.
4. Pin dbt adapter version; thêm `dbt clean`, `parse`, `build`, `docs generate` commands.
5. `source_run_id` là var bắt buộc; macro fail sớm nếu thiếu/invalid.
6. Giữ custom schema naming để model vào đúng `silver`/`gold` mà không sinh schema ghép ngoài ý muốn.

#### P3.2 — Hoàn thiện staging/Silver

Cho mỗi source:

1. Filter đúng một completed `source_run_id`.
2. Rename và cast column rõ ràng.
3. Parse timestamp không im lặng; invalid record phải fail test hoặc được quarantine có reason.
4. Normalize category translation và geography.
5. Aggregate payment trước khi join item.
6. Resolve review multiplicity theo ADR-001 trong `order_reviews_canonical`.
7. Không làm mất source lineage.

#### P3.3 — Kiểm tra Gold core nhập từ `origin/main`

1. Review grain/key từng dimension, fact, bridge và dashboard context view.
2. Chứng minh join không nhân dòng.
3. Sửa relationships test để có `source_run_id` khi historical dimension cần composite key.
4. Kiểm tra `fct_order_item` có đúng một row cho `(source_run_id, order_id, order_item_id)`.
5. Chuyển placeholder `dim_ml_feature` sang deprecation hoặc thay bằng mart P4; không để tên gây hiểu nhầm là hoàn thiện.

#### P3.4 — dbt tests và docs

Thêm:

- `unique`, `not_null`, `relationships`, `accepted_values`, range tests.
- Singular test cho delivered/estimated timestamp, label consistency và join cardinality.
- Source freshness theo ingestion run metadata, không theo tuổi lịch sử Olist.
- Model descriptions, column descriptions, exposure cho ML/API.
- `dbt docs generate` artifact trong CI hoặc release evidence.

**DoD P3:** `dbt build --vars source_run_id=...` đạt trên fixture và full local data; Silver/Gold core có documented grain/key/lineage.

### P4 — Canonical product-item mart

#### P4.1 — Thiết kế schema `gold.ml_modelling_items`

Một row cho mỗi item đủ điều kiện. Nhóm column tối thiểu:

- Keys/lineage: `source_run_id`, `product_item_id`, `order_id`, `order_item_id`.
- Prediction context: `prediction_at`, delivery/estimated timestamps.
- Label: review resolution metadata và `negative`; label fields không nằm trong feature list.
- Item: product, seller, category, price, freight, physical attributes.
- Order/payment: counts, totals, installments, payment complexity.
- Geography/delivery: state/city/distance proxy/duration/slack.
- Historical features: chỉ dữ liệu có event time nhỏ hơn prediction time.
- Weight metadata: `item_count`, `order_weight = 1 / item_count`.
- Quality/version: review-policy version, feature schema version, uncertainty flags.

#### P4.2 — Xây model theo tầng

1. `int_order_payments_aggregated`: một row/order/run.
2. `int_order_reviews_resolved`: một row/order/run theo ADR.
3. `int_item_context`: item + product + seller + order context, không review leakage.
4. `int_historical_seller_features`: point-in-time window, chỉ order trước đó.
5. `int_historical_category_features`: point-in-time window và minimum support.
6. `int_primary_cohort_orders`: delivered, timestamp đủ, on-time/early, reviewed.
7. `gold.ml_modelling_items`: join cuối ở item grain.

Không tính historical aggregate bằng full-dataset groupby. Nếu SQL point-in-time quá tốn chi phí, materialize intermediate theo event date nhưng cutoff vẫn phải kiểm thử.

#### P4.3 — Mart contract tests

- Unique `(source_run_id, order_id, order_item_id)` và `product_item_id` trong run.
- `product_item_id` deterministic.
- Một order chỉ có một inherited label và prediction time.
- `negative` chỉ 0/1; review score resolved 1–5.
- Primary cohort thỏa `delivered_at <= estimated_at`.
- Không có review text/title/time trong feature exposure.
- Item counts trước/sau join bằng nhau.
- Historical feature không dùng event `>= prediction_at`.
- `sum(order_weight)` theo order bằng 1 trong sai số cho phép.

#### P4.4 — Exporter và notebook 02

1. Tạo exporter đọc Gold qua port và ghi atomic Parquet.
2. Manifest gồm source hashes/run ID, row/order counts, schema/dtypes, null profile, cutoff policy, review-policy version, feature schema version và Git SHA.
3. Notebook `02_modelling_dataset.ipynb` chỉ gọi reusable code để validate/visualize; không reimplement join/business rule.
4. So sánh sampled output với dbt mart và fail nếu khác key/row count.
5. Raw/processed data vẫn ignored; chỉ commit schema/summary evidence không chứa private/raw rows.

**DoD P4:** tạo được `data/processed/modelling_items.parquet` và manifest; toàn bộ product-item contract tests đạt.

### P5 — Product-item ML training và nghiên cứu

#### P5.1 — Migrate input schema

1. Version feature lists theo numeric/binary/categorical.
2. Required columns gồm `product_item_id`, `order_id`, target, weight và prediction timestamp.
3. Reject identifier/review/split/unknown columns khỏi matrix.
4. Validate non-empty, unique key, parseable datetime, two-class partitions.
5. Sửa comment/config từ “order-level rebuilt dataset” sang product-item contract.

#### P5.2 — Temporal split theo order

1. Tạo order table duy nhất theo prediction time.
2. Gán partition/fold ở order grain.
3. Join partition trở lại items.
4. Assert zero `order_id` overlap.
5. Báo cáo cả item count, order count, date range và prevalence.
6. Chỉ thay boundary bằng committed config sau khi xem monthly counts; không tune trên final test.

#### P5.3 — Candidate training và weighting

1. Chạy prevalence, Logistic Regression, Random Forest, HistGradientBoosting; CatBoost khi extra có sẵn.
2. Fit preprocessing trong từng fold, không fit toàn dataset.
3. So sánh ít nhất:
   - item rows không weight;
   - `1 / item_count` weight để mỗi order có tổng weight bằng nhau;
   - order-level baseline làm reference.
4. Dùng class weights trước; SMOTE chỉ là ablation sau và phải recalibrate.
5. Bounded hyperparameter search trên rolling-origin validation; cố định seed/parallelism.

#### P5.4 — Selection, calibration và threshold

1. Chọn candidate bằng validation PR-AUC.
2. Dùng segment khác để fit sigmoid/isotonic.
3. So Brier trên held-out calibration comparison segment.
4. Giữ uncalibrated nếu calibration không tốt hơn.
5. Chọn threshold theo policy validation đã khai báo; final test không tham gia.
6. Xác định `medium_from` và `high_from` rõ ràng; không suy ra tùy tiện từ một binary F1 threshold nếu contract cần ba level.

#### P5.5 — Final evaluation hai grain

Item-level:

- PR-AUC, ROC-AUC, Brier, precision/recall/F1, prevalence.

Order-level:

- Aggregate chính xác `max-v1`.
- Cùng metric trên order.
- Recall@budget, precision@budget, low-review order value captured tại 5/10/20%.
- Baseline random, value-only, risk-only, risk × value.

Uncertainty/analysis:

- Bootstrap cluster theo order, không resample item độc lập.
- Calibration curve và PR curve.
- Error/subgroup theo month, category, seller-history/tenure proxy, geography khi sample đủ.
- Global và case-level SHAP với wording phi nhân quả.
- Sensitivity cho multiple review và review observation nếu khả thi.

#### P5.6 — Reproducible artifacts

Mỗi run lưu:

- Frozen config và Git SHA.
- Dataset manifest hash.
- Fold statistics/candidate comparison.
- Selected model/calibrator/threshold policy.
- Item và order test predictions.
- Metrics + order-clustered confidence intervals.
- Figures/tables và environment versions.

Notebook `03` chỉ dựng figure/table từ artifact, không retrain ngầm.

**DoD P5:** một clean run tạo đủ artifact; test set chỉ mở một lần theo recorded workflow; kết quả đáp ứng `docs/research-design.md`.

### P6 — ML release, scoring và web views

#### P6.1 — Thiết kế persistence schema ML

Tạo migration cho:

- `ml.model_releases`.
- `ml.model_thresholds`.
- `ml.predictions` làm header/run đúng tên FK trong Data Dictionary 0.5.
- `ml.item_prediction_scores`.
- `ml.order_prediction_scores`.

Constraint chính:

- Immutable release/version metadata.
- Score trong `[0, 1]`.
- FK item/order prediction về `ml.predictions`.
- Unique item/order trong một run.
- `high_from > medium_from`.
- Order prediction lưu `aggregation_rule = max-v1` và top item.

#### P6.2 — Scoring application use case

1. Port đọc feature mart/model artifact và port ghi predictions.
2. Verify feature schema + artifact hash trước scoring.
3. Score item, map level theo release threshold.
4. Aggregate order bằng pure tested function `max-v1` với deterministic tie-break.
5. Ghi run/item/order trong transaction hoặc staging + promote atomic.
6. Không overwrite release cũ; rerun có run ID mới.

#### P6.3 — Views cho Backend

Tạo và contract-test:

- `ml.v_risk_items_for_web`.
- `ml.v_risk_orders_for_web`.

Fields phải khớp Data Dictionary 0.5. `top_factors` là association/explanation, không gọi causal reason. `synthetic_data_flag=false` cho dữ liệu Olist thật; synthetic chỉ trong demo fixture theo ADR-009.

#### P6.4 — Queue seeding

1. Use case tạo `app.review_cases` từ approved prediction run.
2. Một order tối đa một case; rerun không đổi score snapshot của case cũ.
3. Lưu `prediction_id`, `aggregation_rule`, `original_queued_at` và cycle 1.
4. Seed action idempotent theo release/run policy.

**DoD P6:** model artifact có thể score Gold data, persist item/order predictions, expose hai views đúng contract và tạo case không duplicate.

### P7 — ERD và `app` migrations

#### P7.1 — Chốt ERD vật lý

Duy trì `BA/ERD.md` theo schema runtime. ERD phải thể hiện:

- `app.users`.
- `app.review_cases` 1–N `app.review_cycles`.
- Một active assignment/case tại một thời điểm.
- Cycle 1–N Attempt; Attempt 0–3 evidence.
- Case 1–N comments, decisions và audit events.
- Parameter definition 1–N immutable versions.
- Case tham chiếu immutable prediction snapshot.

Mỗi table ghi grain, PK, FK, unique, check, index, ownership và append-only policy.

#### P7.2 — Migration sequence

Tách migration theo dependency để review được:

1. Extensions/enums hoặc check domains cần thiết.
2. Users và auth support theo ADR-003.
3. Review cases/cycles/assignments.
4. Attempts/evidence/comments/decisions.
5. Audit events.
6. Parameter definitions/versions và initial data.
7. Indexes/views/grants.
8. Demo users/data chỉ ở explicit dev seed, không trong production migration.

#### P7.3 — Database invariants

DB phải bảo vệ được các invariant không phụ thuộc actor/context:

- Unique `order_id` trong review case.
- Partial unique active assignment cho case.
- Unique `(case_id, cycle_no)` và `(cycle_id, attempt_no)`.
- Valid enum/check values.
- Required close fields theo trạng thái bằng check constraint khi khả thi.
- Append-only tables không cấp UPDATE/DELETE cho runtime role.
- Evidence size/type constraint; attachment count và ownership vẫn kiểm ở use case transaction.
- Optimistic `row_version` cho claim/update case.

#### P7.4 — Migration tests

- Apply từ empty database.
- Verify tables/indexes/grants/check constraints.
- Verify runtime role không UPDATE/DELETE append-only tables.
- Verify invalid rows bị DB từ chối.
- Verify migration history và clean second startup.

**DoD P7:** ERD được duyệt, migrations tái lập được toàn bộ `app`, Data Dictionary và schema không lệch nhau.

### P8 — Backend foundation

#### P8.1 — Application skeleton và dependency wiring

1. Tạo FastAPI app factory, settings và lifespan.
2. Tạo async SQLAlchemy engine/session adapter.
3. Wire concrete adapters trong `interfaces/http/dependencies.py`.
4. Không type application service bằng concrete repository như ví dụ chưa hoàn chỉnh của template; constructor nhận domain/application port.
5. Tạo Unit of Work abstraction hoặc transaction runner rõ ràng cho write use cases.
6. Tạo clock/UUID ports và production implementations.

#### P8.2 — Shared domain/API types

1. Domain enums cho role, risk, status, outcome, skip reason, contact result, decision, event type.
2. State transition policy là pure domain code.
3. API DTO strict, `extra='forbid'` cho write request.
4. Pagination query giới hạn `1..100`.
5. Central error mapper trả đúng envelope `{error: {code, message, details}}`.
6. Localized error message catalog `vi`/`en`; code không đổi theo language.
7. Datetime serializer theo ADR-002.

#### P8.3 — Authentication/authorization F11 dependency

1. `POST /auth/login`, `POST /auth/logout`, `GET /me`, `PATCH /me`.
2. Password hash, token expiry/revocation theo ADR-003.
3. `CurrentUser` dependency và role guard.
4. User không tự chọn role; inactive user không đăng nhập.
5. Không trả password hash/token trong logs.
6. Language preference chỉ đổi presentation; không audit như business mutation trừ khi contract được đổi.

#### P8.4 — Test foundation

- Domain/application tests dùng fake repositories/clock/storage.
- API tests dùng dependency override và real Postgres cho repository integration.
- Authentication/403/401/error localization tests.
- OpenAPI snapshot hoặc schema assertions cho API 0.5.

**DoD P8:** app khởi động, health/auth/me hoạt động, architecture tests không cho domain import framework/infrastructure.

### P9 — Backend feature slices F01–F12

Mỗi slice dưới đây phải tuân thứ tự migration/domain/port/use case/adapter/router/test. Các endpoint và field lấy từ `BA/API_CONTRACT.md`.

#### P9.1 — Config, parameter và user queries — F10

**Endpoints:** `GET /config`, `GET /parameters`, `POST /parameters`, `GET /users?role=SPECIALIST`.

Các bước:

1. Tạo `ParameterDefinition`, `ParameterVersion`, effective-value policy.
2. Query active value tại một instant; version tương lai là `SCHEDULED`, cũ là `SUPERSEDED` trong read model.
3. Validate range/unit/allowed enum và cross-rule `capacity_warn < capacity` tại `effective_at`.
4. `POST /parameters` chỉ Manager, reason và future/current effective timestamp theo contract.
5. Insert parameter + `PARAMETER_CHANGE` audit trong cùng transaction.
6. Recalculate derived SLA cho open cases từ effective time bằng deterministic service/job; không rewrite historical events/closed case.
7. `/config` ghép operational parameter với read-only ML thresholds.
8. User query tính `active_count`, `capacity`, `slots_left` nhất quán.

**Tests:** effective-time boundaries, future version, cross-validation, permissions, immutable history, open/closed case behavior.

**DoD:** F10-S01–S04 và API errors đạt; threshold không nằm trong `app.parameters`.

#### P9.2 — Risk Queue, search và filter — F02/F03

**Endpoints:** `GET /orders`, `/orders/summary`, `/orders/filter-options`.

Các bước:

1. Tạo read-only `RiskOrderQueryPort`; adapter join case snapshot + ML views + current assignee/cycle.
2. Implement tất cả filter API 0.5 bằng parameterized query.
3. Validate Order ID prefix/Product Item ID; Product Item search trả `matched_item_id`.
4. Default filter `OPEN`; một order chỉ một row.
5. Default sort: score giảm, SLA gần nhất, aging lâu nhất, cuối cùng `order_id` để stable.
6. Tính `self_claim_allowed`, SLA, aging, stale, escalation ở Backend.
7. Summary `first_pending` tôn trọng role/risk/capacity.
8. Pagination không duplicate/missing trong cùng snapshot query.

**Tests:** combined filters, stable pagination, item search, invalid query, role-aware first pending, no row multiplication.

**DoD:** F02-S01–S05, F03-S01–S05 đạt; Queue và Dashboard dùng cùng metric definitions.

#### P9.3 — Order Detail — F04

**Endpoint:** `GET /orders/{order_id}`.

Các bước:

1. Query order prediction snapshot và item outputs sort score giảm.
2. Load cycles, contacts/evidence, comments, decisions, next step, history, model notes.
3. Manager nhận full audit; Specialist nhận `audit_events=null`.
4. Không expose forbidden review fields hoặc post-prediction feature data trong model context.
5. Top factors thiếu phải trả list rỗng/null đúng contract, không tạo nội dung giả.
6. Xác định available actions ở response hoặc frontend policy từ role/state; Backend vẫn kiểm writes.

**Tests:** not found, Specialist/Manager projection, item-order linkage, latest decision, immutable risk score.

**DoD:** F04-S01–S08 read requirements đạt.

#### P9.4 — Claim, assign và reassign — F05/F08

**Endpoints:** `POST /orders/{id}/claim`, `POST /orders/{id}/assign`.

Các bước:

1. Domain policy: claim chỉ `PENDING` LOW/MEDIUM; HIGH bị từ chối.
2. Capacity lấy tại server clock, không từ request/frontend.
3. Claim dùng conditional update theo expected `row_version`; đúng một winner.
4. Claim tạo assignment, đổi status và audit nguyên tử.
5. Assign chỉ Manager; HIGH được assign; closed case không assign.
6. Reassign đóng assignment cũ và mở assignment mới trong một transaction.
7. Reassign/override capacity bắt buộc reason; override tạo event riêng.
8. Trả order và current user counts mới nhất.

**Tests:** race hai claim thật trên PostgreSQL, capacity boundary, HIGH restriction, stale row version, assignment uniqueness, audit rollback.

**DoD:** không có hai active assignee; slot cập nhật đúng; F05-S01–S05 và F08-S02/S03 đạt.

#### P9.5 — Complete, skip, reopen, comments và model notes — F06/F08

**Endpoints:** `/complete`, `/skip`, `/reopen`, `/comments`, `/model-notes`.

Các bước:

1. State machine chỉ cho transition theo BRD 6.4.
2. Complete bắt buộc valid outcome; `UNREACHABLE` không là outcome.
3. Skip bắt buộc reason; `OTHER` bắt buộc note.
4. Close case: set closed fields, end cycle/assignment, release slot và audit nguyên tử.
5. Reopen chỉ Manager từ closed state; kiểm review confirmation threshold.
6. Reopen tạo cycle mới, reset contact/SLA, giữ original queue/history, status về `PENDING`, assignee null.
7. Comment tối đa 1.000 ký tự, chỉ assignee hoặc Manager, append-only + audit.
8. Model note chỉ Manager, không sửa prediction/risk.

**Tests:** mọi legal/illegal transition, close field validation, slot release, reopen boundary, immutable history, permission.

**DoD:** F06-S01–S04, F08-S01/S04/S05 đạt.

#### P9.6 — Evidence upload và Attempt — F07

**Endpoints:** `POST /files`, `POST /orders/{id}/contacts` và secure evidence download nếu ADR yêu cầu.

Các bước:

1. Tạo `EvidenceStorage` port với local-volume adapter cho dev/test.
2. Stream upload; kiểm MIME bằng content/signature, extension, size; sanitize file name.
3. Upload record ở trạng thái unattached; chỉ uploader/authorized case actor được attach/view.
4. Contact use case lock current case/cycle; verify current assignee + `IN_PROGRESS`.
5. Verify 0–3 unique unattached evidence IDs thuộc user; attach một lần.
6. Validate `contacted_at <= now`, method/result và next date.
7. Allocate `attempt_no` an toàn concurrency; append-only.
8. Nếu attempt cuối `result != REACHED`: insert contact, attach files, close case/cycle/assignment, set `SKIPPED/UNREACHABLE`, audit `CONTACT` + `SKIP` trong cùng transaction.
9. Cleanup unattached file theo retention policy; không xóa evidence đã attach ngoài policy đã duyệt.

**Tests:** MIME spoof, >5 MB, fourth file, reused file ID, wrong assignee, concurrent attempts, max boundary, atomic auto-skip rollback, path traversal.

**DoD:** F07-S01–S07 đạt; không có endpoint update/delete Attempt; file không public tùy ý.

#### P9.7 — Manager Decision — F12

**Endpoint:** `POST /orders/{id}/decisions`; read qua Detail và Queue `needs_decision=true`.

Các bước:

1. Domain entity immutable cho decision.
2. Chỉ Manager; catalogue theo ADR-005.
3. Require non-empty `decision`, `reason`, `next_step`.
4. Optional assignee phải active; due date không quá khứ theo server date/timezone.
5. Gắn current review cycle; append-only.
6. Decision + audit trong cùng transaction.
7. Latest decision projection tạo `next_step`; `needs_decision` tính nhất quán.
8. Decision không tự đổi status, gửi liên hệ hay sửa model output.

**Tests:** permission, required fields, inactive assignee, due date, latest ordering, historical cycles, audit transaction.

**DoD:** F12-S01–S04 đạt.

#### P9.8 — Dashboard và Audit — F01/F09

**Endpoints:** `GET /dashboard`, `GET /audit-events`.

Các bước:

1. Tạo shared filter specification dùng chung Queue/Dashboard.
2. Order view tính totals/rates/level/bands/seller/category/workload/attention/service.
3. Product view join item output sau khi lọc order, tránh nhân metric cấp order.
4. Trend dùng `original_queued_at` và risk level snapshot.
5. Actions engine tạo code/data (`ASSIGN_HIGH`, `REBALANCE`, `STALE`, `DECIDE`, `SELLER_HOTSPOT`), frontend dịch text.
6. Chốt threshold `SELLER_HOTSPOT` qua ADR/parameter trước khi gọi production-ready.
7. Audit query chỉ Manager, read-only, filter/pagination ổn định.
8. Parameter event có `order_id=null`; detail summary không cần N+1 request.

**Tests:** metric reconciliation với Queue, order/product grain, filters, trend totals, role 403, audit immutable/projection, query performance.

**DoD:** F01-S01–S08 và F09-S01–S03 đạt.

#### P9.9 — Backend contract completion

1. Sinh OpenAPI và so endpoint/method/request/response/error với API 0.5.
2. Port hoặc thay `web/Prototype/html/api-check.html` thành automated contract suite.
3. Test CORS/Auth/Accept-Language.
4. Test mọi write tạo đúng audit event và rollback cùng transaction khi fail.
5. Kiểm tra không endpoint nào update ML schema/output.
6. Load-test tối thiểu Queue/Dashboard với dữ liệu gần kích thước Olist; thêm indexes dựa trên `EXPLAIN ANALYZE`, không phỏng đoán.

**DoD P9:** Backend đáp ứng toàn bộ `BA/API_CONTRACT.md` và traceability as-built.

### P10 — Production Angular frontend

#### P10.1 — Bootstrap Angular theo template

1. Tạo Angular current stable được nhóm pin, standalone APIs, strict TypeScript.
2. Cấu hình ESLint, Prettier, Vitest, coverage, environment files và production build budget.
3. App shell, theme tokens, typography, responsive layout, accessible navigation.
4. Core: auth/language/error interceptors, guards, API error mapper.
5. Shared: loading/empty/error/conflict components, badge, pagination, date/currency formatting.
6. Không copy JavaScript stateful prototype vào production; chỉ tái sử dụng visual assets hợp lệ.

Target structure:

```text
src/app/
├── core/
│   ├── auth/
│   ├── api/
│   ├── guards/
│   └── interceptors/
├── shared/
└── features/
    ├── auth/
    ├── queue/
    ├── order-detail/
    ├── attempt/
    ├── decisions/
    ├── dashboard/
    ├── parameters/
    └── audit/
```

#### P10.2 — Typed API client và mock strategy

1. Tạo TypeScript DTO từ OpenAPI hoặc hand-written schema có contract tests; không dùng `any`.
2. API service chỉ transport; mapper chuyển DTO thành ViewModel.
3. Feature facade sở hữu loading/data/error/filter/pagination signals.
4. Development mock phải implement cùng interface, không được có business rule khác Backend.
5. Một environment switch chọn mock/real API; production build không bundle mock data nếu không cần.

#### P10.3 — Login, profile và Language Switch — F11

1. Login form + validation + 401 state.
2. Auth store giữ current user/session theo ADR-003.
3. Guards cho authenticated/Manager routes.
4. Language switch `vi/en`; gửi `Accept-Language`; lưu qua `PATCH /me` sau login.
5. Dịch route labels, buttons, validation, empty/error/status labels; giữ raw user/model text.
6. Test reload preference, fallback, logout và expired token.

**DoD:** F11-S01–S03 đạt; đổi language không tạo business mutation.

#### P10.4 — Risk Queue và Search/Filter — F02/F03

1. Summary banner, active/capacity/slots, suggested first case.
2. Queue table/card đúng cột; một order một row.
3. URL query params là source of truth cho filter/sort để refresh/share được.
4. Search Order ID/Product Item ID, filter chips, reset, filter options.
5. Load more không duplicate; giữ filter/sort.
6. Action visibility theo role/risk/status; conflict `ALREADY_CLAIMED` refresh case/list.
7. HIGH không hiện self-claim cho Specialist.

**Tests:** facade signal transitions, mapper, query serialization, role action policy, component loading/empty/error/conflict.

#### P10.5 — Order Detail — F04

1. Order context/timeline chỉ field được phép.
2. Order score + `max-v1` disclaimer, model/threshold/version metadata.
3. Item list sort score, focus từ Product Item search, synthetic badge.
4. Top factors dùng wording “yếu tố liên quan”, không “nguyên nhân”.
5. Assignment/status/SLA/aging/next step.
6. Timeline Attempt/evidence/comments/decisions/status history; không có edit Attempt.
7. Contextual actions claim/assign/complete/skip/reopen/comment/model-note.
8. Sau mutation patch/refetch state từ response thật, không tự đoán server result.

#### P10.6 — Claim/assign/review/override forms — F05/F06/F08

1. Claim confirmation và capacity warning.
2. Manager assignment modal hiển thị Specialist capacity.
3. Reassign/override reason required; override-capacity warning explicit.
4. Complete form chỉ valid outcome.
5. Skip form chỉ valid reason; `OTHER` bật required note.
6. Reopen confirmation/reason/review-confirmed condition.
7. Comment/model note append-only forms.
8. Map field/server/conflict errors đúng chỗ, không mất user input vô lý.

#### P10.7 — Attempt page — F07

1. Chỉ liệt kê/mở case `IN_PROGRESS` của current Specialist.
2. Reactive form: contacted time, method, result, note, next contact, evidence reference.
3. File picker/drop zone giới hạn type/count/size ở client để UX; Backend vẫn kiểm lại.
4. Upload từng file, giữ file IDs; xử lý partial upload/cancel/retry.
5. Hiển thị attempt/max retry, suggested next date và SLA.
6. Submit một lần; disable duplicate submission.
7. Nếu response auto-skip, hiển thị trạng thái đóng và điều hướng phù hợp.
8. History read-only; evidence mở qua authorized URL/endpoint.

#### P10.8 — Manager Decision page — F12

1. Guard Manager.
2. Danh sách `needs_decision=true`, filter/search.
3. Decision dossier gồm order/item outputs, attempts, evidence, comments.
4. Form required decision/reason/next step; optional assignee/due date/note.
5. Validation và catalogue từ config/contract, không hard-code lệch Backend.
6. Append success vào history, đánh dấu latest, đồng bộ Order Detail.

#### P10.9 — Dashboard — F01

1. Order/Product view switch giữ compatible filters.
2. Metric cards, risk bands, seller/category, workload, attention/action cards.
3. Trend LOW/MEDIUM/HIGH theo ngày.
4. Product top items và synthetic marker.
5. Drill-down tạo đúng Queue URL filters hoặc Order Detail focus.
6. Chart có accessible table/labels, responsive và empty state.

#### P10.10 — Parameters và Audit — F10/F09

Parameters:

- Current/scheduled/history states.
- Typed control theo unit/enum.
- Effective time/reason required và cross-rule feedback.
- Không hiển thị ML thresholds như editable operational parameter.

Audit:

- Manager guard, filters, pagination/timeline.
- Actor/time/type/old/new/reason.
- Read-only hoàn toàn; parameter events hỗ trợ order null.

#### P10.11 — Frontend acceptance

1. Component/facade tests cho mọi feature state.
2. Accessibility scan cơ bản: keyboard, label, focus, contrast, modal focus trap.
3. E2E browser tests với Backend thật cho critical journeys.
4. API checker 0.5 và production build đạt.
5. Prototype được ghi rõ là archived/reference để tránh hai frontend “production”.

**DoD P10:** F01–F12 hiển thị và thao tác đúng role/state; Angular không chứa business-rule authority.

### P11 — End-to-end Compose và vận hành

#### P11.1 — Service graph

Mở rộng `compose.yaml` thành:

```text
postgres -> migrate -> ingest -> dbt -> score/seed
                     postgres -> api -> frontend
                                  |
                           evidence volume
```

Jobs dữ liệu phải explicit profile/command, không tự load full data mỗi lần API start. Service dependencies dùng healthcheck/completion condition, không chỉ startup order.

#### P11.2 — Containers

1. Multi-stage API image, non-root user, chỉ runtime dependencies.
2. Frontend build image + static web server/reverse proxy.
3. dbt/ingest/scoring job images hoặc cùng Python image với command riêng, không cài compiler/notebook vào API runtime.
4. Persistent volumes cho Postgres/evidence; raw Olist read-only.
5. Internal DB port; host ports chỉ bind localhost trong dev.
6. Healthchecks và resource/log limits hợp lý.

#### P11.3 — One-command workflows

Make targets hoặc task equivalents:

- `make bootstrap` — env check, install, DB, migrate.
- `make warehouse` — ingest + dbt build.
- `make train` — canonical training.
- `make score` — release scoring + seed.
- `make app-up` — DB/API/frontend.
- `make e2e` — fixture stack + acceptance tests.
- `make quality` — tất cả static/unit checks.

Mỗi command fail fast khi thiếu raw data/manifest/env; không dùng path ngoài repository.

#### P11.4 — Security và reliability review

- Least-privilege DB roles cho ingest/transform/API/reader.
- CORS allowlist, auth expiry, request size limit.
- Evidence authorization và filename/content handling.
- SQL parameterization, no raw dynamic sort/filter fragments.
- Concurrency tests claim/attempt/parameters.
- Backup/restore smoke test cho Postgres và evidence metadata.
- Không có raw customer/review data trong logs, Git hoặc CI artifacts.

#### P11.5 — E2E acceptance scenarios

1. Specialist login -> filter LOW/MEDIUM -> claim -> add Attempt -> complete.
2. Specialist cannot claim HIGH; Manager assigns HIGH.
3. Two Specialists claim cùng case -> một success, một `ALREADY_CLAIMED`.
4. Capacity full -> claim rejected; Manager override requires reason/audit.
5. Final unsuccessful Attempt -> atomic `SKIPPED/UNREACHABLE`.
6. Manager reopen -> cycle increment, retry/SLA reset, history preserved.
7. Manager adds Decision -> latest appears in Detail and queue no longer `needs_decision` as defined.
8. Scheduled parameter becomes active -> open case derived values update; closed history unchanged.
9. Language switch survives reload and does not change business codes.
10. Dashboard totals reconcile with Queue under same filters.
11. Item scores aggregate exactly to order `max-v1`.
12. Evidence rejects invalid type/size/reuse and remains authorized.

**DoD P11:** clean machine với Docker + repository-local inputs chạy được documented E2E flow; không cần backup repo.

### P12 — Báo cáo, luận văn, demo và release

#### P12.1 — Research evidence freeze

1. Chọn approved dataset run, feature schema, model release và threshold version.
2. Freeze manifest hashes/Git SHA/environment.
3. Chạy final experiment một lần theo protocol.
4. Export versioned tables/figures vào `reports/`.
5. Ghi rõ item weak-label, observed-review selection, no-causality và Olist-period limits.
6. Không dùng metric cũ/order-level artifact như kết quả product-item cuối.

#### P12.2 — Thesis update

Các chương phải đồng nhất với implementation:

- Problem/research question.
- Data and multiple-review policy.
- Product-item grain và order-grouped temporal validation.
- Medallion/dbt lineage.
- Model comparison/calibration/threshold.
- `max-v1` order prioritization và budget evaluation.
- Software architecture Clean Architecture/MVVM.
- Backend/workflow/concurrency/audit.
- Limitations/ethics/non-causal interpretation.

Biểu đồ/bảng phải trỏ tới generated artifact, không chép số thủ công khi có thể automate.

#### P12.3 — Build và validation báo cáo

1. Pin LaTeX toolchain hoặc tạo report-build container có XeLaTeX/Biber.
2. Build từ clean source; resolve warning/reference quan trọng.
3. Kiểm link/citation/figure paths và version labels.
4. Lưu final PDF và build log/version manifest.

#### P12.4 — Demo/defense package

- Seed data rõ synthetic/real và không chứa secret.
- Script 10–15 phút: warehouse lineage -> ML evidence -> Specialist flow -> Manager flow -> audit.
- Slides về research contribution, architecture, limitations và future work.
- Backup screenshots/video khi live environment lỗi.
- Q&A notes cho leakage, weak label, calibration, grouping, `max-v1`, business value và causal limits.

#### P12.5 — Release checklist

- Tag version cho app, model, threshold, aggregation và docs.
- Changelog/migration notes.
- CI xanh toàn bộ.
- No secret/raw data tracked.
- Clean checkout reproducibility verified.
- BRD/FRD/API/Data Dictionary/ERD/OpenAPI/traceability đồng bộ.

**DoD P12:** thesis PDF tái build được, demo E2E chạy được, mọi empirical claim có artifact truy vết.

---

## 9. Pull request breakdown đề xuất

Mỗi PR phải là một vertical increment review được; không tạo một PR “implement whole backend”.

| PR | Nội dung                                        | Phụ thuộc |
| -: | ------------------------------------------------ | ----------- |
| 01 | Commit consolidation baseline                    | —          |
| 02 | Selective import Bronze/dbt/Prototype            | 01          |
| 03 | ADRs + ERD + traceability                        | 01          |
| 04 | Dependency groups, Flyway, CI/Compose foundation | 01          |
| 05 | Bronze migration + loader + tests                | 02, 04      |
| 06 | dbt monorepo adaptation + Silver tests           | 02, 05      |
| 07 | Gold core validation                             | 06          |
| 08 | Product-item mart + contract tests               | 03, 07      |
| 09 | Parquet exporter + notebook 02 + manifest        | 08          |
| 10 | Product-item schema/split/weighting              | 09          |
| 11 | Model selection/calibration/evaluation           | 10          |
| 12 | ML persistence/scoring/views/queue seed          | 11          |
| 13 | App migrations + backend foundation/auth         | 03, 04, 12  |
| 14 | Parameters/config/users                          | 13          |
| 15 | Queue/search/detail reads                        | 13, 14      |
| 16 | Claim/assign/close/reopen                        | 15          |
| 17 | Attempt/evidence/comments                        | 16          |
| 18 | Decisions/dashboard/audit                        | 17          |
| 19 | Backend API 0.5 contract completion              | 14–18      |
| 20 | Angular foundation/auth/i18n                     | 03, 04      |
| 21 | Angular Queue/Detail/workflow                    | 15, 16, 20  |
| 22 | Angular Attempt/Decision                         | 17, 18, 20  |
| 23 | Angular Dashboard/Parameters/Audit               | 14, 18, 20  |
| 24 | Full Compose + E2E/security/performance          | 19, 21–23  |
| 25 | Final experiments/thesis/demo/release            | 24          |

PR có thể chạy song song khi dependency cho phép, nhưng merge order phải giữ migration và contract nhất quán.

## 10. Test matrix tối thiểu

| Khu vực   | Unit                     | Integration               | Contract               | E2E                     |
| ---------- | ------------------------ | ------------------------- | ---------------------- | ----------------------- |
| Bronze     | manifest/checksum        | Postgres load/lock        | manifest schema        | ingest fixture          |
| dbt        | macro khi phù hợp      | `dbt build`             | mart columns/grain     | source-to-Gold          |
| ML         | split/metric/aggregation | synthetic train/artifacts | feature/release schema | Gold-to-prediction      |
| Parameters | effective policy         | repository/transaction    | API error/DTO          | schedule activation     |
| Queue      | filter/sort specs        | SQL projections           | API 0.5                | search/filter/load more |
| Assignment | policy/state             | concurrency/rollback      | errors                 | competing claims        |
| Attempt    | retry/auto-skip          | storage + transaction     | multipart/contact DTO  | upload-to-auto-skip     |
| Decision   | validation/latest        | append/audit              | API 0.5                | manager dossier/submit  |
| Dashboard  | metric functions         | SQL reconciliation        | response schema        | drill-down              |
| Frontend   | mapper/facade/component  | API service               | generated DTO/schema   | actor journeys          |

Các test bắt buộc không được thay bằng manual verification:

- Zero order overlap giữa temporal partitions.
- Point-in-time leakage test.
- Exact `max-v1` reproduction.
- Concurrent claim winner.
- Atomic final Attempt auto-skip.
- Append-only permission enforcement.
- Queue/Dashboard metric reconciliation.
- Role authorization Backend-side.

## 11. Quality gates theo milestone

### Warehouse gate

```bash
dbt parse
dbt build --vars '{source_run_id: "..."}'
```

- Source run completed.
- dbt tests 100% pass.
- Mart row/grain/leakage checks pass.

### Python/Backend gate

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

- Không giảm strict typing để né lỗi.
- Domain unit tests không cần pandas/sklearn/FastAPI/PostgreSQL.
- Integration tests chạy trên migrated PostgreSQL.

### Frontend gate

```bash
npm ci
npm run lint
npm run format:check
npm test
npm run build
```

- Strict TypeScript, không `any` không kiểm soát.
- Coverage threshold được enforce sau baseline.
- Production bundle không chứa secret/mock credential.

### System gate

```bash
docker compose config
docker compose build
make e2e
```

- Health/readiness pass.
- API contract 0.5 pass.
- Critical E2E scenarios pass.
- Relative docs links và thesis build pass.

## 12. Rủi ro và biện pháp kiểm soát

| Rủi ro                                         | Tác động               | Kiểm soát                                             |
| ----------------------------------------------- | ------------------------- | ------------------------------------------------------- |
| Merge `origin/main` ghi đè consolidation    | Mất contract/code mới   | Commit baseline, selective import, PR riêng            |
| Hai pipeline join dữ liệu: notebook và dbt   | Output lệch              | dbt sở hữu mart; notebook chỉ consume/validate       |
| Item rows làm order nhiều item bị overweight | Metric/model sai          | So `1/item_count`, unweighted và order baseline      |
| Leakage historical aggregate                    | Kết quả quá lạc quan  | Event-time cutoff + singular tests + code review        |
| Test final period nhiều lần                   | Selection bias            | Freeze protocol, recorded run, final test gate          |
| Mock và Backend drift                          | FE integration fail       | OpenAPI/API 0.5 automated contract tests                |
| Business rule nằm ở frontend                  | Bypass quyền             | Backend domain/application authority                    |
| Attempt/audit bị sửa                          | Mất truy vết            | Append-only grants + no update/delete endpoints         |
| Race claim/attempt                              | Duplicate ownership/count | row version/lock + real DB concurrency tests            |
| Timezone/SLA không rõ                         | Due date/aging sai        | ADR-002/004 trước implementation                      |
| Evidence upload không an toàn                 | Security/storage leak     | streaming limit, content validation, storage port, auth |
| Dashboard nhân dòng item/order                | Metric sai                | grain-specific query + reconciliation tests             |
| Synthetic data bị hiểu là thật              | Claim sai                 | cờ bắt buộc, fixture-only policy, visible label      |
| Docker/LaTeX chưa có trong WSL                | Không verify release     | CI/containerized build thay local dependency            |

## 13. Completion checklist toàn dự án

### Governance và contracts

- [ ] Consolidation snapshot đã commit/merge.
- [ ] ADR-001–009 đã Accepted.
- [ ] ERD, API 0.5, Data Dictionary 0.5 và OpenAPI đồng bộ.
- [ ] Traceability F01–F12 hoàn chỉnh.

### Data warehouse

- [ ] Bronze loader và migration chạy được.
- [ ] dbt Silver/Gold core đạt full build.
- [ ] `gold.ml_modelling_items` đạt product-item contract.
- [ ] Parquet + manifest tái tạo được.

### ML

- [ ] Product-item training/split/weighting hoàn tất.
- [ ] Calibration, threshold và `max-v1` được version hóa.
- [ ] Item/order metrics + clustered CI + budget evaluation hoàn tất.
- [ ] SHAP/error/subgroup analysis có non-causal wording.
- [ ] ML release/predictions/views được persist và audit được.

### Backend

- [ ] App migrations/roles/grants hoàn tất.
- [ ] Auth/config/users hoàn tất.
- [ ] Queue/search/detail hoàn tất.
- [ ] Claim/assign/status/reopen hoàn tất.
- [ ] Attempt/evidence/comments hoàn tất.
- [ ] Manager Decision hoàn tất.
- [ ] Dashboard/parameters/audit hoàn tất.
- [ ] API contract 0.5 và concurrency tests đạt.

### Frontend

- [ ] Angular foundation/MVVM/Signals hoàn tất.
- [ ] Login/language/guards hoàn tất.
- [ ] F01–F12 pages và states hoàn tất.
- [ ] Accessibility, unit/component và E2E tests đạt.
- [ ] Prototype được đánh dấu reference-only.

### Operations và submission

- [ ] Full Compose stack và one-command workflow chạy được.
- [ ] Security/performance/backup smoke reviews đạt.
- [ ] Experiment artifacts và report figures được freeze.
- [ ] Thesis PDF build reproducibly.
- [ ] Demo/defense package hoàn tất.
- [ ] Clean checkout release validation và tag hoàn tất.

## 14. Tiêu chí “toàn bộ project hoàn thành”

Project chỉ được xem là hoàn thành khi đồng thời thỏa bốn điều kiện:

1. **Research validity:** product-item dataset, order-grouped temporal evaluation, calibration, clustered uncertainty và interpretation limits có artifact tái tạo được.
2. **Product correctness:** F01–F12 đáp ứng BRD/FRD/API 0.5, gồm role, concurrency, append-only, audit, parameter effective time và `max-v1` traceability.
3. **Engineering quality:** Clean Architecture, SOLID/DI, typed contracts, Angular MVVM + Signals, migration-first và testing pyramid được kiểm bằng CI chứ không chỉ mô tả trong tài liệu.
4. **Operational reproducibility:** clean checkout có thể dựng database/warehouse/API/frontend, chạy acceptance flow, build report và truy vết mọi kết quả tới source run, code version, model release và parameter version.

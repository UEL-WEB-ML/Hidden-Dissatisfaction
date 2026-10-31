# Luồng hoạt động của hệ thống Hidden Dissatisfaction

Tài liệu này mô tả hệ thống từ tổng quan đến từng feature để có thể tự vẽ lại kiến trúc hoặc sequence diagram. Nội dung ưu tiên **code đang tồn tại trong repository**; yêu cầu mục tiêu chưa khớp hoàn toàn với code được ghi riêng ở phần cuối.

## 1. Hệ thống giải quyết bài toán gì?

Hệ thống tìm các đơn Olist đã giao đúng hoặc sớm nhưng vẫn có nguy cơ nhận review thấp. Model chấm điểm ở cấp **product item**, sau đó tổng hợp thành rủi ro cấp **order**. Các order rủi ro được đưa vào queue để Specialist xem xét; Manager phân công, giám sát và ghi quyết định.

Hai nguyên tắc quan trọng:

1. Review gốc chỉ tồn tại ở cấp order. Item score là rủi ro review thấp của order trong bối cảnh item, không chứng minh item gây bất mãn.
2. Model chỉ ưu tiên case cho con người. Hệ thống không tự động liên hệ hoặc đưa ra hành động với khách hàng.

## 2. Bức tranh tổng thể

Hệ thống có hai luồng chính độc lập về thời điểm chạy.

### 2.1. Offline data/ML flow

```text
9 Olist CSV files
  → kiểm tra tên file, header và SHA-256
  → nạp snapshot bất biến vào PostgreSQL Bronze
  → dbt: Bronze → Silver → Intermediate → Gold
  → gold.ml_modelling_items (mỗi dòng là một product item)
  → export modelling_items.parquet
  → temporal training + model selection + calibration + threshold
  → versioned model artifact
  → release scoring từng product item
  → max-v1 aggregation theo order
  → ghi item predictions + order risk vào PostgreSQL
  → tạo nguồn dữ liệu cho Risk Queue
```

Đây là các job **explicit/opt-in**. API khởi động không tự ingest, train hoặc score.

### 2.2. Online human-review flow

```text
Specialist / Manager
  → NGINX phục vụ Angular SPA và proxy /api
  → Angular gửi REST/JSON + Bearer JWT
  → FastAPI xác thực và kiểm tra role
  → Application use case
  → Domain policy kiểm tra luật nghiệp vụ
  → PostgreSQL adapter đọc/ghi transaction
  → audit event được thêm cùng transaction ghi
  → response trả về Angular
  → UI cập nhật queue/detail/dashboard
```

### 2.3. Điểm nối giữa hai luồng

Offline scoring ghi model output vào schema `ml`. Online API đọc projection risk order kết hợp với workflow state trong schema `app`. Workflow được phép thay đổi assignment, status, contacts, comments và decisions, nhưng **không có endpoint sửa score hoặc risk level**.

## 3. Các khối kiến trúc

| Khối | Trách nhiệm | Công nghệ |
|---|---|---|
| Browser UI | Màn hình, form, state hiển thị, guard theo role | Angular |
| Web server | Phục vụ static SPA, chuyển `/api` đến backend | NGINX |
| Delivery/API | Parse request, auth, role check, gọi use case, map lỗi | FastAPI |
| Application | Điều phối use case và khai báo port | Python |
| Domain | State machine, capacity, retry, reopen, validation | Python thuần |
| Infrastructure | PostgreSQL query/transaction, file evidence, model artifact | psycopg, SQLAlchemy/asyncpg |
| Operational database | User, workflow, audit, warehouse và predictions | PostgreSQL |
| Data transformation | Xây cohort, feature và Gold mart | dbt-postgres |
| ML | Train, calibration, threshold, scoring | pandas, scikit-learn, CatBoost |
| Runtime | Khởi động postgres → migrate → API → frontend | Docker Compose |

## 4. Actor, quyền và trạng thái

### 4.1. Actor

**Specialist**:

- xem queue và order detail;
- tự claim case LOW/MEDIUM nếu còn capacity;
- thêm contact attempt cho case mình đang giữ;
- upload evidence;
- complete/skip case mình đang giữ;
- thêm comment.

**Manager**:

- có các quyền đọc nghiệp vụ;
- assign/reassign mọi risk level;
- override capacity khi có lý do;
- reopen case;
- xem dashboard và audit;
- cấu hình parameter;
- ghi model note và Manager Decision.

### 4.2. State machine của case

```text
                       Manager reopen
                  ┌────────────────────┐
                  │                    │
PENDING ──claim/assign──> IN_PROGRESS ─┼──complete──> COMPLETED
                                      └──skip──────> SKIPPED
```

- `PENDING`: chưa có người xử lý.
- `IN_PROGRESS`: đã có active assignee.
- `COMPLETED`: đóng với outcome hợp lệ.
- `SKIPPED`: đóng với skip reason hợp lệ.
- Reopen tạo review cycle mới, reset assignee/contact counter/SLA của cycle; lịch sử cũ vẫn giữ nguyên.

## 5. Luồng dùng chung của mọi request

1. `AuthStore` lấy token từ `localStorage`.
2. Angular interceptor thêm `Authorization: Bearer ...` và `Accept-Language`.
3. NGINX chuyển request `/api/v1/...` tới FastAPI.
4. Dependency `current_user` giải mã token và tải user.
5. Route kiểm tra role nếu feature chỉ dành cho Manager/Specialist.
6. Route chuyển DTO thành command/filter và gọi service.
7. Domain policy từ chối action sai bằng mã ổn định như `INVALID_STATE`, `CAPACITY_FULL`.
8. Infrastructure adapter lock/read/write PostgreSQL trong transaction.
9. Với workflow write, audit event được ghi trong cùng transaction.
10. FastAPI map domain error thành HTTP 403/404/409/422 và envelope `{error:{code,message,details}}`.
11. Angular facade/store chuyển response thành signal để UI render loading, success, empty hoặc error state.

## 6. Chi tiết từng feature

## F00 — Authentication, session và profile

### Mục đích

Xác định người dùng, role và ngôn ngữ trước khi vào workspace.

### Login

```text
Login form
  → POST /api/v1/auth/login {username, password}
  → AuthenticationService kiểm tra credential
  → trả JWT + User
  → token lưu localStorage: hd_access_token
  → language lưu localStorage: hd_language
  → chuyển tới /queue
```

- Sai credential: `401 INVALID_CREDENTIALS`.
- `authGuard` chỉ kiểm tra có token ở frontend.
- Khi app phục hồi session, `GET /auth/me` xác nhận token và tải user.
- Nếu API trả 401, interceptor xóa session.
- `managerGuard` đưa non-manager về `/queue`.

### Logout

`POST /auth/logout` được gọi, sau đó frontend luôn xóa token/user local và chuyển `/login`. Backend hiện dùng stateless JWT nên endpoint logout không lưu blacklist.

### Language/Profile

- Đổi ngôn ngữ gọi `PATCH /auth/me {preferred_language: vi|en}`.
- UI lưu lựa chọn local ngay, backend lưu preference theo user.
- Profile hiện chỉ đọc tên, username, role và preferred language.

### Thành phần để vẽ

`User → LoginComponent → AuthStore → ApiClient → FastAPI Auth → User store → JWT → Browser localStorage`.

---

## F01 — Risk Overview Dashboard

### Mục đích

Cho Manager xem sức khỏe toàn queue và phân bổ nguồn lực.

### Luồng

1. Manager mở `/dashboard`; `managerGuard` kiểm tra role phía UI.
2. `DashboardFacade` giữ filter mặc định: `view=order`, `days=7`, `status=OPEN`.
3. UI gọi `GET /api/v1/dashboard` với các filter tương thích.
4. FastAPI bắt buộc role Manager và validate:
   - `days`: trống, 1, 3 hoặc 7;
   - `view`: `order` hoặc `product`.
5. `CaseReads.dashboard` query PostgreSQL projection và tính response tổng hợp.
6. UI hiển thị totals, risk distribution, trend, seller/category concentration và specialist workload.
7. Khi đổi filter/view, facade merge filter mới và tải lại toàn bộ dashboard.

### Input/filter

`days`, `level`, `seller`, `category`, `assignee`, `status`, `product_item`, `view`.

### Output nghiệp vụ

- Order view dùng grain order/case.
- Product view dùng grain product item.
- KPI và chart phải dùng cùng filter và grain.
- Dashboard là read-only; drill-down sẽ dẫn sang Queue hoặc Order Detail.

### Thành phần để vẽ

`Manager → DashboardComponent → DashboardFacade → GET /dashboard → CaseReads → PostgreSQL ml/app projections`.

---

## F02 + F03 — Risk Queue, search và filter

### Mục đích

Queue là màn hình vận hành chính: tìm, ưu tiên và chọn case cần xử lý.

### Luồng tải trang

Khi mở `/queue`, `QueueStore.load()` chạy ba request:

1. `GET /orders`: danh sách phân trang.
2. `GET /orders/summary`: banner HIGH pending, case đề xuất, capacity/slot của user.
3. `GET /orders/filter-options`: danh sách seller/category để tạo filter.

Store giữ `orders`, `total`, `summary`, `options`, loading/error/conflict. `hasMore` đúng khi số dòng hiện tại nhỏ hơn `total`.

### Filter và sort

Queue hỗ trợ:

- tìm theo order/product-item ID: `q`;
- risk level: `level`;
- trạng thái, mặc định `OPEN`;
- seller, category, assignee;
- `needs_decision`;
- SLA: over/soon/escalated/stale;
- sort theo priority/SLA/aging;
- `limit`, `offset`.

Backend tạo `QueueFilters`, validate và query projection risk queue. Mặc định nghiệp vụ là ưu tiên score, sau đó SLA/aging theo query implementation.

### Load more

1. Offset mới bằng số item hiện có.
2. Request giữ nguyên filter.
3. Response được nối vào list.
4. Store loại trùng theo `order_id`.

### Action theo role

- Specialist thấy claim khi case PENDING, LOW/MEDIUM và còn capacity.
- HIGH không cho tự claim; phải do Manager assign.
- Manager dùng assign/reassign trong Order Detail.
- Bấm một dòng mở `/orders/:orderId`.

### Thành phần để vẽ

`User → QueueComponent → QueueStore → [orders + summary + options] → RiskOrderQuery/OperationalReads → PostgreSQL projection`.

---

## F04 — Order Detail

### Mục đích

Tập hợp toàn bộ context của một case mà không trộn model output với workflow state.

### Luồng đọc

1. Route `/orders/:orderId` lấy ID từ URL.
2. `OrderDetailStore` gọi `GET /orders/{orderId}`.
3. API gọi `CaseReads.detail(order_id, now, include_audit)`.
4. Manager nhận thêm audit data; Specialist nhận phần detail cần thiết.
5. Mapper frontend đổi DTO thành view model.

### Các vùng dữ liệu

**Model output, chỉ đọc**:

- order risk score/level;
- aggregation rule `max-v1`;
- top item và danh sách item;
- top factors, model/threshold version, predicted time;
- synthetic data flag.

**Order context**:

- seller/category/customer location;
- order value/freight;
- các timestamp được phép tại prediction time.

**Workflow state**:

- status, assignee, outcome/skip reason;
- cycle, SLA, aging, contact count;
- contacts/evidence, comments, decisions, model notes, next step.

### Các action phát sinh từ detail

- Claim;
- assign/reassign;
- complete/skip;
- reopen;
- comment;
- model note;
- chuyển sang Add Attempt hoặc Manager Decision.

Sau mutation thành công, frontend đóng form và reload detail để lấy projection mới nhất.

### Thành phần để vẽ

`OrderDetailComponent → OrderDetailStore + OrderActionsFacade → API → CaseReads/WorkflowCommands → app + ml schemas`.

---

## F05 — Claim, assign và reassign

### A. Specialist claim

```text
Specialist clicks Claim
  → POST /orders/{id}/claim
  → verify role = SPECIALIST
  → lock case / conditional claim
  → validate PENDING + unassigned
  → reject HIGH
  → count active assignments vs capacity
  → create assignment + set IN_PROGRESS
  → append CLAIM audit
  → return updated order + active_count/capacity/slots_left
```

Các lỗi chính:

- HIGH: `403 HIGH_RISK_REQUIRES_ASSIGN`;
- đầy capacity: `422 CAPACITY_FULL`;
- người khác claim trước: `409 ALREADY_CLAIMED`;
- state đã đổi: `409 INVALID_STATE`.

### B. Manager assign/reassign

1. UI tải users và chỉ hiện active Specialist.
2. Manager chọn assignee, reason và tùy chọn override capacity.
3. `POST /orders/{id}/assign`.
4. Backend lock case bằng `FOR UPDATE`.
5. Kiểm tra target là active Specialist.
6. Lấy advisory transaction lock theo assignee để tránh hai assignment đồng thời vượt capacity.
7. Đếm active assignments và đọc parameter `capacity` đang hiệu lực.
8. Reassign bắt buộc reason; vượt capacity chỉ được phép khi Manager bật override và có reason.
9. Release assignment cũ, insert assignment mới, set `IN_PROGRESS`.
10. Ghi `ASSIGN`/`REASSIGN`; nếu override thì ghi thêm `OVERRIDE`.

Mọi bước DB nằm trong một transaction.

---

## F06 — Complete, skip và trạng thái

### Complete

`POST /orders/{id}/complete {outcome,note}`.

- Chỉ case `IN_PROGRESS`.
- Specialist phải là assignee; Manager có thể close.
- Outcome hợp lệ: `HAS_ISSUE`, `NO_ISSUE`, `DUPLICATE`.
- Backend set `COMPLETED`, lưu outcome/note/closed_at.
- Release active assignment và close review cycle.
- Ghi audit `STATUS`.

### Skip

`POST /orders/{id}/skip {reason,note}`.

- Cùng permission/state như complete.
- Reason: `UNREACHABLE`, `DUPLICATE`, `REFUSED`, `NOT_APPLICABLE`, `OTHER`.
- `OTHER` bắt buộc note.
- Backend set `SKIPPED`, release assignment, close cycle và ghi audit `SKIP`.

### Tính nguyên tử

Nếu update case, release assignment, close cycle hoặc audit lỗi thì transaction rollback; không để case đóng nhưng assignment vẫn active.

---

## F07 — Contact Attempt, retry, evidence và auto-skip

### Điều kiện vào feature

Trang `/orders/:orderId/attempt` chỉ cho sửa khi:

- user là current assignee;
- case đang `IN_PROGRESS`.

Frontend vẫn disable form, nhưng backend kiểm tra lại độc lập.

### Upload evidence

1. User chọn tối đa 3 file.
2. Frontend kiểm tra PNG/JPG/PDF và tối đa 5 MB/file.
3. Mỗi file gọi riêng `POST /api/v1/files` multipart field `file`.
4. Backend chỉ cho Specialist upload.
5. Backend đọc tối đa `MAX_EVIDENCE_BYTES + 1` và nhận diện loại bằng file signature, không tin MIME client.
6. File được lưu vào evidence volume; metadata upload lưu DB ở trạng thái chưa attach.
7. API trả `file_id`; frontend đợi tất cả upload hoàn tất.

### Ghi contact

1. Frontend gửi `POST /orders/{id}/contacts` gồm thời điểm, method, result, note, next date và các `file_id`.
2. Backend kiểm tra Specialist và current assignee.
3. Validate method, result, thời điểm không ở tương lai, next date và số file.
4. Lock case và lấy open review cycle.
5. Đếm attempts trong **cycle hiện tại** và đọc `max_contact` đang hiệu lực.
6. Lock từng evidence upload, đảm bảo file thuộc user, chưa từng attach và ID không trùng.
7. Insert attempt append-only; attach evidence; đánh dấu upload đã dùng.
8. Ghi audit `CONTACT`.
9. Nếu đây là attempt cuối và result khác `REACHED`, cùng transaction tự:
   - đóng case thành `SKIPPED/UNREACHABLE`;
   - release assignment và close cycle;
   - ghi thêm audit `SKIP`.
10. Response trả contact mới và order state mới; UI cập nhật timeline.

Evidence upload chưa gắn attempt sẽ được job `purge-evidence` xóa sau retention mặc định 24 giờ.

---

## F08 — Manager Override, reopen, comment và model note

### Reopen

`POST /orders/{id}/reopen {reason,review_confirmed}` chỉ dành cho Manager.

1. Case phải là `COMPLETED` hoặc `SKIPPED`.
2. Reason luôn bắt buộc.
3. Nếu case đóng quá `reopen_review_days` hoặc đã reopen đủ `reopen_review_times`, cần `review_confirmed=true`.
4. Backend đọc SLA theo risk level và parameter bundle hiện hành.
5. Tạo review cycle mới với `cycle_no + 1`, `started_at`, `sla_due_at` và parameter version.
6. Reset case về `PENDING`, bỏ assignee/outcome/close data, tăng reopen count.
7. Giữ original queue time, contacts và audit cũ.
8. Ghi `REOPEN` audit.

### Comment

- Assignee hoặc Manager gọi `POST /orders/{id}/comments`.
- Nội dung 1–1000 ký tự.
- Append-only, không có sửa/xóa.
- Ghi `COMMENT` audit.

### Model note

- Chỉ Manager gọi `POST /orders/{id}/model-notes`.
- Note được ghi thành audit `MODEL_NOTE`.
- Không cập nhật bảng prediction, score hoặc level.

---

## F09 — Audit History

### Mục đích

Cho Manager trả lời ai làm gì, lúc nào, trên case nào và vì sao.

### Luồng

1. Mở `/audit`, manager guard kiểm tra UI.
2. `AuditFacade` gọi `GET /audit-events`.
3. API bắt buộc role Manager.
4. Query theo `event_type`, `actor_id`, `order_id`, `override_only`, `limit`, `offset`.
5. Response có `items`, `total`; UI phân trang bằng offset.

Audit là read-only. Không có route update/delete. Event gồm actor, timestamp, old/new value, reason và order summary. Các workflow write ghi audit trong cùng transaction với state change.

---

## F10 — Parameter Configuration

### Đọc parameter

Manager gọi `GET /parameters`. Response phân biệt current items và history/scheduled versions. UI tính riêng danh sách `status=SCHEDULED`.

### Tạo version mới

1. Manager nhập key, typed value, `effective_at`, reason.
2. `POST /parameters`.
3. Backend kiểm tra role và tạo `CreateParameterVersionCommand` kèm actor/time.
4. Service validate key, range, cross-constraint và thời điểm hiệu lực.
5. Ghi version mới thay vì sửa version cũ.
6. Sau success, frontend reload toàn bộ parameter list.

Parameter ảnh hưởng capacity, contact limit, SLA và reopen policy. History không bị sửa/xóa. Job `recalculate-sla` dùng khi cần áp dụng thay đổi SLA cho open review cycles.

---

## F11 — Language Switch

1. Người dùng chọn `vi` hoặc `en` ở app shell.
2. `AuthStore` cập nhật `hd_language` trong localStorage ngay.
3. Nếu đã login, frontend gọi `PATCH /auth/me` để lưu preference.
4. Mọi request sau có `Accept-Language` mới.
5. Backend hiện localize validation message ở một số boundary; mã enum và dữ liệu gốc không đổi.

Language switch không tạo workflow event và không thay đổi model/business data.

---

## F12 — Manager Decision

### Decision queue

1. Manager mở `/decisions`.
2. Frontend gọi `GET /orders?needs_decision=true`.
3. Có thể tìm order/product item và lọc risk level.
4. Chọn case mở `/orders/:orderId/decision`.

### Decision workspace

1. Tải order detail làm dossier: status, owner, cycle, top signal, contacts/evidence/comments và decision history.
2. Tải user list cho optional next-step assignee.
3. Manager nhập:
   - decision;
   - reason;
   - next step;
   - assignee tùy chọn;
   - due date tùy chọn;
   - note tùy chọn.
4. Gọi `POST /orders/{id}/decisions`.
5. Domain kiểm tra decision code, reason, next step và due date không ở quá khứ.
6. Backend kiểm tra optional assignee là active user.
7. Decision được gắn với review cycle mới nhất, insert append-only.
8. Ghi audit `DECISION`.
9. Decision **không tự đổi status, assignment hoặc score**.
10. UI prepend decision mới vào history và hiển thị làm latest next step.

Decision codes: `NO_FURTHER_ACTION`, `FOLLOW_UP_CUSTOMER`, `WORK_WITH_SELLER`, `REFER_AFTER_SALES`.

## 7. Chi tiết offline data và ML features

## D01 — Bronze manifest

Command: `make bronze-manifest`.

1. Kiểm tra đúng 9 filename trong allowlist.
2. Đọc và so sánh chính xác header từng CSV.
3. Từ chối CSV lạ.
4. Stream từng file để tính SHA-256.
5. Ghi manifest deterministic vào `data/interim/bronze-manifest.json`.

Mục đích là chứng minh chính xác raw snapshot nào được sử dụng.

## D02 — Bronze ingestion

Command: `make ingest`, cần `BRONZE_DSN` và manifest.

1. Đọc manifest.
2. Build lại manifest từ file hiện tại.
3. So filename, destination table và checksum.
4. Stream CSV, đổi empty string thành NULL.
5. Nạp snapshot vào Bronze và lưu run/provenance.
6. Nếu file thay sau khi tạo manifest, checksum mismatch và ingestion dừng.

## D03 — dbt warehouse

Command: `make warehouse` chạy Compose profile `jobs`.

```text
Bronze source
  → Silver: typed/cleaned source
  → Intermediate: cohort + feature groups + quality rules
  → Gold: product-item modelling mart
```

Gold authoritative là `gold.ml_modelling_items`. dbt tests kiểm tra grain, invariant, reconciliation và leakage-related contracts.

## D04 — Export modelling snapshot

CLI `export-modelling-items` đọc Gold theo `source_run_id`, ghi Parquet và metadata gồm source hashes, cutoff policy, review policy, feature schema và git SHA. Snapshot này tách training khỏi live database và làm experiment reproducible.

## M01 — Training và model selection

Command `hidden-dissatisfaction train`; `make train` cố ý yêu cầu caller cung cấp `TRAIN_COMMAND`.

1. Validate modelling schema.
2. Grouped temporal split theo `order_id`; item cùng order không được rơi vào partition khác nhau.
3. Tạo rolling-origin folds trên development period.
4. Train candidate models/regimes trên từng fold.
5. Đánh giá item average precision và order-level `max-v1` PR-AUC/Brier.
6. Trên selection period, chọn candidate theo:
   - order max-v1 PR-AUC cao nhất;
   - Brier thấp hơn để tie-break;
   - model đơn giản hơn nếu vẫn hòa.
7. Fit calibration candidates và chọn calibration method.
8. Chọn threshold trên threshold partition theo capacity policy.
9. Ghi selection record và lock.
10. Sealed test chỉ được mở khi `--finalize-test`, frozen selection record và test lock khớp.
11. Ghi metrics, predictions và artifact/version metadata.

## M02 — Release scoring

1. Validate release ID, aggregation rule, source schema và thresholds.
2. Load artifact và xác minh SHA-256/schema/feature order.
3. Validate runtime model input và giá trị finite.
4. Hash chính xác ordered model inputs để truy vết.
5. `predict_proba` tạo score cho mỗi `product_item_id`.
6. Group item theo `order_id`.
7. `max-v1` chọn item score cao nhất làm order score/top item.
8. Gán LOW/MEDIUM/HIGH theo versioned thresholds.
9. Atomic writer ghi item rows, order rows, release/source metadata và input hash.
10. Online projection đọc kết quả này để tạo risk queue.

## 8. Dữ liệu nên thể hiện khi tự vẽ

### Các data store logic

- Raw Olist CSV files.
- Bronze immutable snapshot + ingestion run.
- Silver/Intermediate/Gold dbt models.
- Parquet modelling snapshot.
- Versioned model artifact + metrics + selection record.
- `ml` item/order predictions.
- `app.review_cases` và review cycles.
- assignments, attempts, evidence, comments, decisions.
- audit events và parameter versions.
- evidence file volume.

### Các đường mũi tên quan trọng

- Màu xanh lá: user-facing online request.
- Màu xanh dương: raw-to-Gold data flow.
- Màu cam: training/scoring/release flow.
- Màu tím: evidence/audit/governance.
- Nét đứt: job hoặc integration khác lifecycle; không phải synchronous request.

## 9. Gợi ý chia diagram để không bị rối

Không nên đưa mọi chi tiết vào một canvas. Nên vẽ bốn diagram:

### Diagram A — System context

Chỉ gồm Actor, Angular/NGINX, FastAPI, PostgreSQL, Offline ML pipeline và evidence volume. Tối đa 8–10 node.

### Diagram B — Offline ML lifecycle

CSV → manifest → Bronze → dbt → Gold → export → train → artifact → score → predictions/risk queue.

### Diagram C — Online case lifecycle

Login → Queue → Claim/Assign → Detail → Attempt → Complete/Skip → Manager Decision/Reopen. Đặt state machine ngay dưới flow.

### Diagram D — Một workflow write transaction

Angular form → API route → auth/role → application command → domain validation → PostgreSQL lock/update → audit append → response. Có thể dùng assign hoặc contact làm ví dụ.

## 10. Những điểm cần ghi chú vì code và contract chưa khớp hoàn toàn

1. `GET /orders` và `GET /orders/filter-options` trong `api/app.py` hiện không khai báo dependency `current_user`, dù contract nói mọi request ngoài login phải authenticated. Khi vẽ kiến trúc mục tiêu, vẫn đặt chúng sau auth boundary; khi mô tả current code cần đánh dấu gap này.
2. `ApiClient.users()` khai báo nhận `UserDto[]`, trong khi backend `GET /users` trả `{items:[...]}`. Đây là contract mismatch cần sửa trước khi coi assign/decision user picker là ổn định end-to-end.
3. Frontend login dùng interval để chờ token thay vì điều hướng trực tiếp theo observable completion. Đây là implementation detail, không cần đưa vào architecture diagram.
4. API contract document vẫn có một số đoạn lịch sử/mock. Nguồn current behavior đáng tin hơn là routes, domain policies, PostgreSQL adapters và frontend facades hiện tại.
5. `make train` và `make score` không chứa promoted command mặc định; release operator phải truyền command cụ thể.
6. Model training/output migration sang product-item là contract authoritative, nhưng README vẫn cảnh báo một số historical artifact/output cũ còn order-level. Không dùng artifact cũ để minh họa release hiện hành nếu chưa xác minh metadata.

## 11. Code map để kiểm tra khi vẽ

| Nội dung | File chính |
|---|---|
| Frontend routes/role guard | `frontend/hidden-dissatisfaction-frontend/src/app/app.routes.ts` |
| HTTP client | `frontend/hidden-dissatisfaction-frontend/src/app/core/api-client.service.ts` |
| Auth/session | `frontend/hidden-dissatisfaction-frontend/src/app/core/auth.store.ts` |
| Queue | `frontend/hidden-dissatisfaction-frontend/src/app/features/queue/queue.store.ts` |
| Order actions | `frontend/hidden-dissatisfaction-frontend/src/app/features/order-detail/order-actions.facade.ts` |
| Attempt/evidence | `frontend/hidden-dissatisfaction-frontend/src/app/features/attempt/attempt.facade.ts` |
| API composition/routes | `src/hidden_dissatisfaction/api/app.py` |
| Workflow routes | `src/hidden_dissatisfaction/api/workflow_routes.py` |
| Domain state/policies | `src/hidden_dissatisfaction/domain/workflow.py` |
| Transactional workflow writes | `src/hidden_dissatisfaction/infrastructure/postgres_workflow_commands.py` |
| Bronze contract | `src/hidden_dissatisfaction/application/bronze_ingestion.py` |
| CLI/jobs | `src/hidden_dissatisfaction/interfaces/cli.py` |
| Training | `src/hidden_dissatisfaction/modeling/training.py` |
| Release scoring | `src/hidden_dissatisfaction/application/release_scoring.py` |
| Runtime services | `compose.yaml` |
| Operational commands | `Makefile` |

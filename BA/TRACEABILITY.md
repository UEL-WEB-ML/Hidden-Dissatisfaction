# As-built traceability and double-check record

## 1. UI → API → persistence

| Flow | UI | API | Policy/adapter | Persistence | Status |
|---|---|---|---|---|---|
| Authentication | login/profile/common | auth login/logout/me | auth service | users | Implemented |
| Queue/filter | index | orders, summary, options | QueueFilters, PostgresRiskOrderQuery | cases + active/historical case ML views | Implemented |
| Claim | index/order | order claim | validate_claim, claim adapter | cases, assignments, audit | Implemented |
| Assignment | order | order assign | validate_assign, commands | cases, assignments, audit | Implemented |
| Detail | order | order detail | PostgresCaseReads | workflow + ML views | Implemented, reduced commerce DTO |
| Contact/evidence | attempt | files, contacts | evidence policy, add_contact | uploads, attempts, evidence, audit | Implemented |
| Complete/skip/reopen | order/attempt | complete, skip, reopen | workflow policies | cases, cycles, assignments, audit | Implemented |
| Comments/model notes | order | comments, model-notes | validate_comment | comments/audit | Implemented |
| Manager decision | decision | decisions | validate_decision | decisions/audit | Implemented |
| Dashboard | overview | dashboard | build_dashboard/read model | cases, attempts, ML views | Implemented with frontend normalization |
| Audit | audit | audit-events | audit read model | audit_events | Implemented; actor-kind projection caveat |
| Parameters | settings | config/parameters | parameter domain/service | parameters, bundles, audit | Implemented |
| SLA recalculation | no UI | CLI job | PostgresSlaRecalculator | sla_adjustments | Manual job only |
| Training/scoring | no UI | CLI/batch adapters | modeling/release scoring | artifacts + ML tables | Manual/offline; no promoted real demo artifact |
| Prediction supersession | no UI | queue seed batch | case snapshot guard + seed adapter | predictions, immutable cases | Existing cases remain actionable; existing orders skipped |

## 2. Loop 1 — source extraction

Đã đối chiếu:

1. Runtime OpenAPI `/openapi.json`: 26 paths, 28 operations; gồm ba health paths
   và 23 business/auth paths.
2. Runtime PostgreSQL `information_schema`: 220 columns thuộc 24 app/ml relation/view.
3. Schema-only dump của `app` và `ml`, migrations V001–V022.
4. `frontend/prototype/js/api.js` và 9 HTML screens.
5. Domain policies: queue, workflow, parameter, case metrics.
6. Runtime responses của config, parameters, queue detail, dashboard và audit.

Các tài liệu được viết lại từ các nguồn trên; không copy field target-only từ bộ
draft cũ.

## 3. Loop 2 — reverse verification result

Thực hiện ngày 2026-11-02 bằng cách đọc ngược tài liệu và so với cùng runtime
snapshot của Loop 1.

| Check | Kết quả thực tế |
|---|---|
| 28/28 OpenAPI operations xuất hiện trong API Contract | Pass |
| 24/24 app/ml table/view xuất hiện trong Data Dictionary hoặc ERD | Pass |
| 220/220 tên cột vật lý xuất hiện trong Data Dictionary | Pass |
| Role/màn hình đúng navigation và backend guards | Pass |
| Queue enums/filter đúng domain `QueueFilters` | Pass |
| Workflow enum/rule đúng `domain/workflow.py` | Pass |
| 14/14 parameter key đúng `domain/parameters.py` | Pass |
| Link nội bộ trong `BA/` tồn tại | Pass |
| `git diff --check -- BA` | Pass |
| Known gaps không bị mô tả là implemented | Pass |
| Authenticated Specialist/Manager walkthrough | Pass trước khi tạo tài liệu |

## 4. Known as-built issues — không được che trong tài liệu

1. Audit API map provenance thành actor_kind.
2. Status history không gồm DECISION.
3. Parameter version label khác nhau giữa config và parameter list.
4. BUSINESS_HOURS chưa được dùng trong phép tính SLA backend.
5. First-touch SLA chưa có enforcement.
6. Retry gap do frontend đề xuất, backend không enforce interval.
7. Logout không revoke JWT phía server.
8. Error localization và 500 envelope chưa đầy đủ.
9. Public Order/Item DTO không trả đầy đủ commerce attributes.
10. Local Olist demo score không phải model inference.
11. Online training, scheduler và automatic model promotion chưa có.

## 5. Change control

Mọi thay đổi endpoint/schema/policy phải cập nhật tài liệu tương ứng trong `BA/`
và chạy lại hai nhóm kiểm tra:

1. Static/contract: Ruff, Black, Mypy, unit/contract, frontend static/security.
2. Runtime: migrations, PostgreSQL integration, smoke và authenticated walkthrough.

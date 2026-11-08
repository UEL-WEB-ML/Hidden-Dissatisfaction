# Traceability matrix

`Implemented` means code and a test target exist. It does not replace P11
runtime/E2E evidence required to close a release.

| BRD rule | FRD | API | DB | Backend | Frontend | Test target | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Risk overview | F01 | `GET /dashboard` | ML views, cases, audit | `postgres_case_reads.py` | dashboard | `test_workflow_routes.py` | Implemented; runtime pending |
| Queue | F02 | `GET /orders`, `/orders/summary` | cases, assignments | `queue.py` | queue | `test_queue.py` | Implemented; runtime pending |
| Search/filter | F03 | `/orders/filter-options` | ML views | `postgres_risk_queue.py` | queue | `test_workflow_routes.py` | Implemented; runtime pending |
| Detail | F04 | `GET /orders/{id}` | cases, cycles, attempts | `postgres_case_reads.py` | order-detail | `test_workflow_routes.py` | Implemented; runtime pending |
| Claim | F05 | `/claim` | cases, assignments, audit | `claim.py` | order actions | `test_p9_policies.py` | Implemented; concurrency pending |
| Complete/skip | F06 | `/complete`, `/skip` | cycles, assignments | `workflow_commands.py` | order actions | `test_workflow.py` | Implemented; runtime pending |
| Attempt/evidence | F07 | `/files`, `/contacts` | attempts, evidence | workflow adapter | attempt | `test_workflow_routes.py` | Implemented; storage pending |
| Assignment/reopen | F08 | `/assign`, `/reopen` | assignments, cycles | `workflow_commands.py` | order actions | `test_p9_policies.py` | Implemented; runtime pending |
| Audit | F09 | `GET /audit-events` | audit events | case reads | audit | `test_workflow_routes.py` | Implemented; runtime pending |
| Configuration | F10 | `/config`, `/parameters`, `/users` | parameters | `parameters.py` | parameters | `test_parameters.py` | Implemented; runtime pending |
| Authentication | F11 | `/auth/*`, `/me` | users | `auth.py` | auth/profile | `test_api_foundation.py` | Implemented; runtime pending |
| Decision | F12 | `/decisions` | decisions, audit | workflow commands | decision | `test_workflow_routes.py` | Implemented; runtime pending |

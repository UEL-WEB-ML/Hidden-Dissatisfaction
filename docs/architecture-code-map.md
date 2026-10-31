# Architecture code map

## Scope

I am mapping the current runtime, warehouse, and ML delivery paths in order to produce an editable Excalidraw system-architecture diagram.

I am not mapping notebook-internal analysis steps, individual SQL columns, every HTTP endpoint, or legacy diagrams under `web/SoDo/`.

## Entry points

- `frontend/hidden-dissatisfaction-frontend/src/app/app.routes.ts:6` — Angular enters through login, queue, order-detail, decision, dashboard, audit, parameters, and profile routes.
- `src/hidden_dissatisfaction/api/app.py:120` — `create_app` constructs the FastAPI delivery boundary and its production adapters.
- `src/hidden_dissatisfaction/api/workflow_routes.py:147` — the workflow router exposes case reads, assignments, outcomes, evidence, dashboard, and audit operations.
- `src/hidden_dissatisfaction/interfaces/cli.py:101` — the CLI enters data ingestion, modelling export, training, scoring-support, and SLA jobs.
- `Makefile:33` — `bootstrap` starts PostgreSQL and applies migrations.
- `Makefile:43` — `warehouse` runs the dbt build through the opt-in Compose jobs profile.
- `Makefile:46` — `train` runs an explicitly supplied training command.
- `Makefile:50` — `score` runs an explicitly supplied scoring command.
- `Makefile:57` — `app-up` starts API and frontend after bootstrap.

## Call graph

```text
Specialist / Manager
  -> Angular feature routes                         app.routes.ts:6-18
  -> FastAPI auth, queue and workflow routes        api/app.py:203-421
  -> application services and domain policies       docs/architecture.md:7-14
  -> PostgreSQL production adapters                 api/dependencies.py:24-73
  -> app/ml operational tables and evidence volume  compose.yaml:42-58

Olist CSV files
  -> validated Bronze manifest and ingestion        application/bronze_ingestion.py:20-180
  -> dbt Silver / Intermediate / Gold                dbt/models/intermediate/int_p4_cohort.sql:11-16
  -> gold.ml_modelling_items                         dbt/models/gold/ml_modelling_items.sql:23-24
  -> model training and artifact selection           modeling/training.py:167-223
  -> item scoring + max-v1 order aggregation         application/release_scoring.py:112-165
  -> predictions / risk queue in PostgreSQL          infrastructure/postgres_release_scoring.py:59-137
  -> FastAPI queue and workflow UI                   api/app.py:289-421
```

## Surprises

- `README.md:70` — the checked-in product-item contract is authoritative, while some historical generated training output is still order-level.
- `Makefile:46-52` — training and scoring deliberately require caller-supplied commands instead of running implicitly.
- `src/hidden_dissatisfaction/api/app.py:106` — application construction has a development JWT fallback, while production Compose supplies `HD_JWT_SECRET` at `compose.yaml:49`.
- `compose.yaml:55-56` and `compose.yaml:73-74` — API and frontend ports bind to localhost, not all host interfaces.

## Open questions

- Which concrete `TRAIN_COMMAND` and `SCORE_COMMAND` are promoted for the final release? — inspect deployment/runbook configuration outside the checked-in Make defaults.
- Should the diagram later split the operational PostgreSQL schemas into a physical ERD? — inspect `infra/postgres/migrations/` if a database-level diagram is required.
- Should notebook-only exploratory transformations be shown? — inspect notebooks only if the diagram scope expands beyond the production path.

## Editable diagram

- Generate the local artifact with `node scripts/generate_architecture_excalidraw.mjs`.
- Open `docs/system-architecture.excalidraw` in the Excalidraw web app or desktop app. The file is self-contained: its technology-logo SVGs are embedded in the Excalidraw scene.
- Source SVGs are kept in `docs/assets/architecture-icons/` so a regenerated diagram remains reproducible. They cover only technologies evidenced in the repository: Angular, NGINX, FastAPI, Python, Docker, PostgreSQL, dbt, scikit-learn, and CatBoost.
- The generated scene has 63 elements and three visual clusters: online review flow, explicit offline data/ML delivery, and a compact reading guide. Solid arrows show the two primary flows; dashed arrows identify cross-cluster integrations.
- The diagram does not embed `.env` values, database URLs, passwords, or JWT secrets. It reflects the current API, Angular routes, Compose services, dbt models, training, and release-scoring code; `web/SoDo/` is intentionally out of scope.

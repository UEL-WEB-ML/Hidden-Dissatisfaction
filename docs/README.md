# Documentation index

This repository is the single source of truth for the Hidden Dissatisfaction project.

## Research contract

1. [`problem_statement_olist_hidden_dissatisfaction.md`](problem_statement_olist_hidden_dissatisfaction.md)
2. [`research-design.md`](research-design.md)
3. [`data-contract.md`](data-contract.md)
4. [`modeling-training-plan.md`](modeling-training-plan.md)
5. [`architecture.md`](architecture.md)
6. [`end_to_end_machine_learning_theory_olist_hidden_dissatisfaction.md`](end_to_end_machine_learning_theory_olist_hidden_dissatisfaction.md)

## Product and integration contract

1. [`BRD_olist_hidden_dissatisfaction.md`](BRD_olist_hidden_dissatisfaction.md) — BRD 4.2
2. [`FRD_olist_hidden_dissatisfaction.md`](FRD_olist_hidden_dissatisfaction.md) — FRD 2.2
3. [`API_CONTRACT_olist_hidden_dissatisfaction.md`](API_CONTRACT_olist_hidden_dissatisfaction.md) — API 0.5
4. [`DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md`](DATA_DICTIONARY_web_olist_hidden_dissatisfaction.md) — Data Dictionary 0.5

## Operations and evidence

- [`local-development.md`](local-development.md) — Python, data and PostgreSQL setup.
- [`P12-gate-2-demo.md`](P12-gate-2-demo.md) — synthetic Gate 2 walkthrough, capture fallback, and defense notes.
- [`evidence/P12-gate-0-release-boundary.md`](evidence/P12-gate-0-release-boundary.md) — evidence statuses, demo scope, provenance rules, and the P5 replacement-holdout gate.
- [`evidence/P5-development-gate-2026-10-23.md`](evidence/P5-development-gate-2026-10-23.md) — development-only evidence record.
- [`consolidation-manifest.md`](consolidation-manifest.md) — imported sources, exclusions and migration boundary.
- [`report-olist-hidden-dissatisfaction-literature-review-2026-09-26.md`](report-olist-hidden-dissatisfaction-literature-review-2026-09-26.md) — literature review.
- [`../references/`](../references/) — dated research-source snapshots.
- [`../web/BaoCao_LaTeX/`](../web/BaoCao_LaTeX/) — report source.
- [`../web/SoDo/`](../web/SoDo/) — diagrams.
- [`../web/Wireframe/`](../web/Wireframe/) — archived/reference-only static wireframe; not an active application path.

The delivered static frontend is [`../frontend/prototype/`](../frontend/prototype/). This documentation
does not claim browser E2E coverage for that frontend.

## Fixed system decisions

- ML grain: product item.
- Workflow, temporal split and bootstrap grain: order.
- Product items inherit the containing order's observed review label; this is a weak label, not causal attribution.
- Initial order aggregation: `max-v1`.
- Prediction time: immediately after delivery confirmation and before review information is used.
- Canonical raw-data path: `data/raw/olist/`.
- Canonical processed target: `data/processed/modelling_items.parquet` after the product-item migration is implemented.
- PostgreSQL schemas: `app`, `bronze`, `silver`, `gold`, `ml`.

Files in the former `ML_docs` and `Docker_Environment` repositories are backups, not active contracts.

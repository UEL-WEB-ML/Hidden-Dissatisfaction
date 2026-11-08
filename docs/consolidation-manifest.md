# Repository consolidation manifest

Date: 2026-10-21

## Source of truth

`Hidden-Dissatisfaction` is the only active repository for this project. The former `ML_docs` and `Docker_Environment` repositories remain unchanged as local backups and must not receive new project changes.

## Imported snapshot

From `ML_docs`:

- BRD 4.2, FRD 2.2, API Contract 0.5 and Data Dictionary 0.5 (later retired
  after the implementation-based `BA/` set was established);
- product-item problem statement and end-to-end ML theory;
- dated research-source snapshots under `references/`;
- LaTeX report sources and diagrams under `web/`.

From `Docker_Environment`:

- PostgreSQL bootstrap roles, schemas and default privileges;
- environment template and Compose service definition.

The Compose paths were rewritten for this repository. The database and Compose project names were changed from the old `ironman` codename to `hidden_dissatisfaction`.

## Deliberately excluded

- `ds_with_ai_capstone` and all of its reported metrics;
- Git histories from the source repositories;
- raw Olist data, local virtual environments, caches and generated model artifacts;
- generated `web/BaoCao_LaTeX/main.pdf` and LaTeX build files;
- general learning notes outside the agreed Hidden Dissatisfaction research/product contract.

## Known migration boundary

The as-built product contract is maintained in `BA/`. Research and modeling
documents may describe target work, but they are not evidence that training or
release functionality has been implemented.

No source repository should be deleted until the team has reviewed and committed this consolidated snapshot.

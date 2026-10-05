# Engineering rules for Hidden Dissatisfaction

These rules adapt the TinyBigCorp Clean Architecture template and the AMS backend engineering foundations to an ML research repository. Apply patterns when they solve a real boundary; do not create abstractions or empty folders only to imitate an enterprise backend.

## Priorities

1. Reproducibility over convenient one-off results.
2. Temporal integrity over optimistic model scores.
3. Explicit contracts over notebook magic.
4. Maintainability over short-term speed.
5. Honest research claims over impressive wording.

## Architecture

- `domain`: pure Python research concepts, eligibility rules, invariants, and domain errors. It must not import pandas, scikit-learn, FastAPI, SQLAlchemy, or infrastructure modules.
- `application`: use cases, commands/results, and ports needed by those use cases. It may depend on `domain`, never on concrete infrastructure.
- `infrastructure`: Olist readers, dataframe transformations, model implementations, artifact stores, and external tooling. Adapters implement application ports.
- `interfaces`: CLI, notebooks, and a future API. Interfaces parse input, call a use case, and format output; they contain no cohort, feature, or model logic.

Dependencies point inward. Inject external dependencies through constructors. Define an ABC/Protocol for replaceable boundaries such as dataset sources, model trainers, and artifact stores—not for every helper function.

## ML and research invariants

- The prediction time is `order_delivered_customer_date`.
- The primary population contains only delivered, on-time/early orders.
- No feature may use review text, review timestamps, review score, or information first available after prediction time.
- Fit preprocessing only on the training fold. Never fit encoders, imputers, selectors, or calibrators on validation/test data.
- Use chronological splits for primary results. A random split may appear only as a clearly labeled sensitivity analysis.
- Preserve probabilities. Do not apply SMOTE by default; any resampling is an ablation and requires probability recalibration and comparison against a non-resampled baseline.
- Report PR-AUC and calibration alongside threshold metrics. Accuracy alone is not an acceptable primary result.
- Keep model selection data separate from final temporal test data.
- Version the feature schema, experiment configuration, random seed, data fingerprint, and model artifact together.
- Treat “review 1–2 among observed reviews” as the primary label. Never treat a missing review as a satisfied customer.
- Risk and SHAP values are associative, not causal. Never call captured order value “saved value” without treatment outcome data.

## Python rules

- Python 3.11+; public functions/classes have type hints and docstrings.
- Classes use `PascalCase`; functions and variables use `snake_case`; constants use `UPPER_CASE`.
- Prefer immutable dataclasses/value objects for domain concepts.
- Raise meaningful domain errors; do not leak raw parser/library exceptions across boundaries.
- Avoid mutable global state and hidden notebook state.
- Keep functions focused. Use classes when identity, state, polymorphism, or dependency injection provides clear value.
- Format with Black (100 columns), lint with Ruff, and type-check with MyPy strict mode.

## Notebook rules

- Notebooks are consumers of `src`, not the source of reusable business or modeling logic.
- Number notebooks by purpose (`01_...`, `02_...`) and make execution order explicit.
- Restart-and-run-all must succeed against documented inputs.
- Do not commit embedded secrets, raw datasets, large model binaries, or unnecessary cell output.
- Promote stable transformations/evaluation code into `src` and cover it with tests.

## Testing

- Unit tests: domain rules, feature availability, split logic, metrics, and application orchestration.
- Integration tests: Olist schema parsing, joins, preprocessing pipelines, artifact serialization, and deterministic inference.
- Acceptance tests: a small end-to-end temporal train/evaluate/predict slice using synthetic fixtures.
- Test happy paths, exclusions, malformed timestamps, missing reviews, duplicate keys, schema drift, and leakage guards.
- Coverage is a signal, not proof. Tests must trace to a research invariant or contract.

## Workflow for a new slice

1. State the research question, input grain, prediction time, output, and failure cases.
2. Add/update the contract in `docs/`.
3. Implement domain rules and unit tests.
4. Define the smallest application port/use case needed.
5. Implement infrastructure adapters and integration tests.
6. Wire CLI/notebook entry points.
7. Run Ruff, Black, MyPy, and Pytest.
8. Record the experiment and update documentation.

Do not scaffold every future model or web endpoint in advance. Add a folder/module when the next vertical slice needs it.

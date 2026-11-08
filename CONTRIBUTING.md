# Contributing

## Before coding

1. Read `docs/README.md`, `docs/research-design.md`, and `docs/data-contract.md`.
2. Write down the prediction-time impact of every proposed feature.
3. Keep changes scoped to one reproducible vertical slice.

## Local checks

```bash
uv run ruff check .
uv run black --check .
uv run mypy src tests
uv run pytest --cov=hidden_dissatisfaction --cov-report=term-missing
```

## Pull request checklist

- [ ] No raw data, credentials, or large generated artifacts are committed.
- [ ] New public code is typed and documented.
- [ ] Tests cover the relevant research invariant and failure path.
- [ ] Feature computation is valid at delivery time and fit only on training data.
- [ ] Product items from one `order_id` remain in the same temporal split and bootstrap cluster.
- [ ] Order outputs reproduce the declared versioned aggregation rule (`max-v1` initially).
- [ ] Metrics include minority-class and calibration evidence where applicable.
- [ ] Research claims remain predictive/associational unless causal identification exists.
- [ ] Documentation and experiment configuration are updated.

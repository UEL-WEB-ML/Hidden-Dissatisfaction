# Reports

Commit only report-ready, reasonably sized tables and figures that can be reproduced from a versioned configuration. Exploratory figures may remain under `notebooks/figures` until promoted.

`notebooks/03_model_evaluation.ipynb` is artifact-only. It calls
`hidden_dissatisfaction.modeling.reporting.render_report`, which reads the sealed
JSON report and saved item/order prediction CSVs and writes deterministic PNG,
PDF, and SVG figures under `reports/figures`, plus CSV and Markdown tables under
`reports/tables`. It never trains or fits a model. Scores are presented as
priority/ranking signals unless the saved artifact documents calibration; item
labels are inherited from order reviews and are not causal evidence. SHAP is
unavailable unless saved SHAP artifacts are supplied.

---
title: "Verified books, official documentation, and engineering guides"
retrieved: 2026-09-26
status: "manual fallback after research APIs were unavailable"
---

# Production ML books and engineering sources

## Books and open courses

- Huyen, C. (2022). *Designing Machine Learning Systems: An Iterative Process for Production-Ready Applications*. O'Reilly Media. Verified from the author's MLOps guide: https://huyenchip.com/mlops/
- Molnar, C. (2025). *Interpretable Machine Learning*, 3rd edition. Open book: https://christophm.github.io/interpretable-ml-book/
- Murphy, K. P. (2022). *Probabilistic Machine Learning: An Introduction*. MIT Press. Open book page: https://probml.github.io/pml-book/book1.html
- Full Stack Deep Learning (2022 course). Covers when to use ML, development infrastructure, testing, data management, deployment, continual learning and monitoring: https://fullstackdeeplearning.com/course/2022/
- Mohandas, G. *Made With ML*. End-to-end curriculum organized as design, data, modeling, testing, reproducibility, deployment and monitoring: https://madewithml.com/

## Official engineering documentation

- Google, "Rules of Machine Learning": https://developers.google.com/machine-learning/guides/rules-of-ml
  - Start with a simple model and trustworthy end-to-end pipeline.
  - Measure first, optimize second.
  - Reuse transformations between training and serving.
  - Test on future data and monitor silent failures.
- scikit-learn, "Common pitfalls and recommended practices": https://scikit-learn.org/stable/common_pitfalls.html
  - Split before fitting preprocessing; put transformations and estimator in one Pipeline.
  - Never learn preprocessing, feature selection or thresholds from the test set.
- scikit-learn, "Probability calibration": https://scikit-learn.org/stable/modules/calibration.html
  - A score of 0.8 is useful only if about 80% of similarly scored cases are positive.
  - Calibration must use data independent of base-model fitting.
- scikit-learn, "Tuning the decision threshold": https://scikit-learn.org/stable/modules/classification_threshold.html
  - Probability estimation and action selection are separate problems.
  - Tune thresholds on validation data against the real utility, never on the training or final test data.
- Feast, "Point-in-time joins": https://docs.feast.dev/getting-started/concepts/point-in-time-joins
  - Reconstruct feature values as they were available at each event timestamp.
  - Filter by creation timestamp to prevent later backfills from leaking into historical rows.
- MLflow, "Model Registry": https://mlflow.org/docs/latest/ml/model-registry/
  - Registry provides model lineage, versions, aliases, tags and controlled promotion or rollback.
- Great Expectations, "Try GX Core": https://docs.greatexpectations.io/docs/core/introduction/try_gx/
  - Express data assumptions as executable expectations and checkpoints.
- Evidently, "Data drift" and "Model monitoring": https://docs.evidentlyai.com/metrics/explainer_drift and https://www.evidentlyai.com/ml-in-production/model-monitoring
  - Monitor software health, input quality, prediction distributions, delayed model quality and business outcomes as separate layers.
  - Drift is a diagnostic signal, not proof that model performance has declined.

## Design implication for this thesis

The smallest defensible system is a reproducible batch pipeline rather than a real-time microservice. It should produce a versioned table of scores and explanations, support a human review queue, and later join delayed review labels for monitoring. This architecture matches the small public dataset and avoids infrastructure that does not contribute to the research questions.

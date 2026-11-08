---
title: "Verified papers for end-to-end risk ML"
retrieved: 2026-09-26
status: "manual fallback after research APIs were unavailable"
---

# Verified academic sources

## Imbalanced evaluation

- Saito, T., & Rehmsmeier, M. (2015). "The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets." *PLOS ONE*, 10(3), e0118432. DOI: https://doi.org/10.1371/journal.pone.0118432
- Verified claim: PR curves expose the reliability of positive predictions under class imbalance, while ROC curves can look deceptively good because the large negative class dominates specificity.

## Probability calibration

- Niculescu-Mizil, A., & Caruana, R. (2005). "Predicting Good Probabilities with Supervised Learning." *ICML 2005*. Stable PDF: https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). "On Calibration of Modern Neural Networks." *ICML 2017*. https://proceedings.mlr.press/v70/guo17a.html
- Murphy, A. H. (1973). "A New Vector Partition of the Probability Score." *Journal of Applied Meteorology*, 12(4), 595-600. DOI: https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2
- Verified claim: ranking quality and probability quality are different properties. A separate calibration set or cross-validated calibration is needed because calibrating on training predictions produces optimistic probabilities.

## Explainability

- Lundberg, S. M., & Lee, S.-I. (2017). "A Unified Approach to Interpreting Model Predictions." *Advances in Neural Information Processing Systems 30*. arXiv: https://arxiv.org/abs/1705.07874
- Verified claim: SHAP assigns additive feature-attribution values to individual predictions. Attribution explains model behavior, not causal effects in the real world.

## Production readiness

- Sculley, D., et al. (2015). "Hidden Technical Debt in Machine Learning Systems." *NIPS 2015*, 2503-2511. https://research.google/pubs/hidden-technical-debt-in-machine-learning-systems/
- Breck, E., Cai, S., Nielsen, E., Salib, M., & Sculley, D. (2017). "The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction." *IEEE Big Data 2017*. https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/
- Verified claim: production ML quality depends on data, pipelines, tests, monitoring, lineage and feedback loops, not only on the model artifact.

## Retrieval notes

The configured Parallel and OpenRouter API keys were unavailable. Every source above was therefore checked against the publisher, conference, arXiv or Google Research page before inclusion.

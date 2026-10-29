# P5 accuracy-plan deliberate-stop analysis

Date: 2026-10-29

## Outcome

The bounded accuracy plan stopped below its development target. The retained global winner is
`order_weight:random_forest-depth8-leaf5-v1` with rolling order PR-AUC `0.146502`, rolling Brier
`0.190663`, and selection-holdout order PR-AUC `0.210761`. Bounded CatBoost GPU tuning improved
the single selection holdout to `0.223873`, but its rolling PR-AUC was lower at `0.145813`.

## Evidence from the completed waves

- Seller speed/variability, order composition, and product morphology/content are the only retained
  packages. Leave-one-group-out reduced rolling PR-AUC by `0.004152`, `0.005027`, and `0.002032`.
- Target history, geography, payment, calendar/volume, data-quality, and controlled-interaction
  packages failed their frozen development gates.
- Direct order aggregation and bounded GPU CatBoost candidates did not beat the retained model on
  the primary rolling metric.
- The best result remains far below the `0.25` stop target. Additional local tuning is therefore
  more likely to select development noise than to resolve the signal limitation.

## Likely limiting factors

1. The review label is observed at order level and inherited by every item, creating item-level
   label noise when an order contains multiple products or sellers.
2. The point-in-time feature contract intentionally excludes post-review evidence and therefore
   cannot observe several product-quality and service-failure causes represented in review text.
3. Seller/category history has sparse-support and drift constraints; aggressive target encoding
   would increase leakage risk rather than provide reliable generalization.
4. Variation across temporal folds and the failure of richer models indicate limited stable signal,
   not merely insufficient estimator capacity.

## Decision boundary

Accuracy work is closed as a deliberate stop under the plan's Definition of Done. Further work
requires an explicit research-design change: genuinely new prediction-time data, an independently
measured target, order-level estimand redesign, or a two-stage review-observation sensitivity model.
It must not reuse the historical final-test partition for selection.

P12 still blocks confirmatory claims because no genuinely untouched replacement holdout has been
authorized or recorded. Existing and future runs on the disclosed historical test period remain
`exploratory_non_confirmatory`.

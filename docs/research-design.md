# Research design contract

## Main question

Among product items in Olist orders delivered on time or early, how well can a calibrated model using only information available at delivery time estimate the risk that the containing order receives an observed 1–2 star review, and how well do versioned item scores aggregate into an order-level priority queue compared with simple baselines?

## Estimand and scope

- ML unit: one product item, uniquely identified by `product_item_id = order_id + '-' + order_item_id`.
- Workflow and split unit: one delivered order. Every item from an order must remain in the same temporal partition.
- Prediction time: immediately after `order_delivered_customer_date`.
- Primary population: orders delivered no later than `order_estimated_delivery_date`.
- Primary outcome: review score in `{1, 2}` among orders with a review. Each item inherits its containing order's label because Olist does not identify which item caused the review.
- Secondary outcome: review observation itself.
- Generalization scope: the observed Olist period only unless external validation is added.

The item score estimates the conditional risk of a low review for the containing order in the context of that item. It is not an item-specific satisfaction label and must not be interpreted as evidence that the item caused dissatisfaction. Order risk is the maximum item score under the initial versioned aggregation rule `max-v1`. The primary model estimates observed conditional risk, not latent dissatisfaction for all customers. A two-stage sensitivity analysis may model review observation and low review conditional on observation separately.

## Permitted feature families

- order and payment information available by delivery;
- item, seller, product, and category attributes;
- customer/seller geography;
- price, freight, item count, seller count, and payment complexity;
- absolute delivery duration and on-time slack known at delivery;
- historical aggregate features computed strictly from earlier events.

## Forbidden inputs

- review score, text, title, creation time, or answer time;
- actions/outcomes recorded after review;
- full-dataset aggregate encodings;
- any historical aggregate whose cutoff is later than the target order prediction time.

## Validation and model comparison

1. Sort/split orders by delivery prediction time, then assign all product items from each order to the same partition.
2. Reserve the latest period once as a final test set.
3. Select features, hyperparameters, and calibration on earlier rolling folds.
4. Fit every transformer on each training fold only.
5. Start with prevalence and Logistic Regression; then Random Forest and one boosting family.
6. Compare no-resampling/class-weight/threshold strategies first. Treat SMOTE as an ablation.
7. Fit calibration on data not used to fit the underlying estimator.

## Required evidence

- order and product-item counts, label prevalence, and date ranges by time split;
- item-level PR-AUC and `max-v1` order-level PR-AUC with order-clustered bootstrap confidence intervals;
- minority precision, recall, and F1 at declared thresholds;
- ROC-AUC as a secondary metric;
- Brier score and calibration curve;
- order-level recall@budget and value-captured@budget at 5%, 10%, and 20%;
- comparisons against random and value-only policies;
- global and case-level SHAP with non-causal wording;
- error analysis by time, category, seller tenure, and geography where sample size permits.

## Interpretation boundaries

- Missing review does not mean satisfaction.
- Low review does not equal churn or lost profit.
- Risk score does not identify treatment response.
- Captured risky order value is prioritization utility, not saved revenue.
- Feature importance and SHAP are not causal effects.

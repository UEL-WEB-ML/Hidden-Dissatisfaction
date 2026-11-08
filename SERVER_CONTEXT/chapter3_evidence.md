# Chapter 3 evidence

## 1. Order-grouped temporal split

Every item belonging to an order remains in the same partition. Intervals are left-closed and right-open. Counts and positive-label prevalence below come from `reports/experiments/p5-s6-e15-content.json`; test outcomes are redacted.

| Partition | Observed prediction-time range | Orders | Items | Positive prevalence |
|---|---|---:|---:|---:|
| Train | 2016-10-11 13:46:32 to 2017-09-30 20:09:53 | 23,545 | 26,708 | 10.1318% |
| Selection | 2017-10-01 11:52:06 to 2017-11-30 23:59:03 | 8,586 | 9,957 | 11.9213% |
| Calibration fit | 2017-12-01 00:28:05 to 2018-01-31 23:58:36 | 11,759 | 13,444 | 12.7417% |
| Calibration comparison | 2018-02-01 00:04:20 to 2018-03-31 21:55:48 | 10,623 | 12,265 | 13.7954% |
| Threshold selection | 2018-04-01 12:36:43 to 2018-05-31 19:05:39 | 12,351 | 14,319 | 11.6139% |
| Sealed test | 2018-06-01 10:52:03 to 2018-08-30 23:58:44 | 18,561 | 21,191 | redacted |

Configured boundaries end at 2017-10-01, 2017-12-01, 2018-02-01, 2018-04-01, 2018-06-01, and 2018-09-01. Three rolling-origin folds are formed inside train.

## 2. Cohort funnel

No stepwise cohort-count log is persisted. A dbt build log does prove that the snapshot was rebuilt to 97,884 rows; see `label_snapshot_build_evidence.md`. This read-only re-derivation uses the currently present Olist CSVs and the canonical-review rule (answered review first; then latest answer/creation; then review ID) in `dbt/models/intermediate/int_p4_cohort.sql`.

| Stage | Orders | Product items |
|---|---:|---:|
| All orders | 99,441 | 112,650 |
| `order_status = delivered` | 96,478 | 110,197 |
| Delivered on/before estimated date | 88,644 | 101,475 |
| Valid observed review after delivery | 85,420 | 97,878 |

The retained modeling snapshot manifest reports **85,425 orders / 97,884 items**, six items and five orders more than this re-derivation. Use this funnel with that caveat; a run-specific label-generation log is needed for exact reconciliation. Re-derived eligible-order positive prevalence is 7,865 / 85,420 = **9.2074%**.

## 3. Calibration isolation

Calibration uses an isolated fit period (2017-12-01 to 2018-02-01) and later comparison period (2018-02-01 to 2018-04-01). The base estimator is fitted on train + selection; sigmoid and isotonic calibrators fit only on calibration-fit, then compete by Brier score on calibration-comparison.

For the retained Random Forest run, comparison Brier was: none 0.220332, isotonic 0.105665, sigmoid **0.104947**; sigmoid was selected. No calibration fitting or threshold choice uses test.

## 4. Training configuration and retained model

- Seed 42; `n_jobs=1`; resampling none.
- Candidate families: prevalence, logistic regression, Random Forest, HistGradientBoosting, optional CatBoost GPU challenger.
- Declared variants: prevalence-v1; logistic C=0.1/C=1; Random Forest depth 8 leaf 5 / depth 12 leaf 10; HistGradientBoosting L2=1 leaf 31 / L2=5 leaf 15; CatBoost GPU depth 8; native CatBoost GPU depth 8.
- Regimes: item-unweighted, order-weight, order-reference, order-aggregate.
- Retained development model: `order_weight:random_forest-depth8-leaf5-v1`.
- Parameters: 200 trees; `max_depth=8`; `min_samples_leaf=5`; `max_features=sqrt`; `class_weight=balanced_subsample`; Gini; bootstrap enabled; `random_state=42`; `n_jobs=1`.
- GPU device 0 applies only to the CatBoost challenger; the retained model is CPU Random Forest.

## 5. Final retained feature schema

The seven retained groups yield 61 features; type is numeric, binary, or categorical.

| Group | Type | Features |
|---|---|---|
| Baseline | Numeric | `price`, `freight_value`, `payment_count`, `payment_amount`, `max_payment_installments`, `seller_prior_review_count`, `seller_prior_review_score_avg`, `category_prior_review_count`, `category_prior_review_score_avg`, `estimated_delivery_buffer_days`, `purchase_to_delivery_days`, `carrier_to_delivery_days`, `product_photos_qty`, `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm`, `order_item_count`, `order_item_value_total`, `item_value_share` |
| Baseline | Binary | `seller_history_low_support_flag`, `category_history_low_support_flag` |
| Baseline | Categorical | `product_category`, `customer_state` |
| Seller speed/variability | Numeric | `seller_mean_approval_to_carrier_days`, `seller_mean_carrier_to_delivery_days`, `seller_mean_purchase_to_delivery_days`, `seller_std_purchase_to_delivery_days`, `seller_delivery_cv`, `seller_mean_freight_value_ratio`, `seller_std_freight_value_ratio` |
| Order composition counts | Numeric | `order_seller_count`, `order_category_count`, `order_product_count`, `order_unique_product_count` |
| Order composition counts | Binary | `multi_item_flag`, `multi_seller_flag`, `multi_category_flag` |
| Order composition ratios | Numeric | `order_freight_total`, `order_freight_share`, `order_max_item_value_share`, `order_min_item_value_share` |
| Order composition concentration | Numeric | `order_category_hhi`, `order_seller_hhi` |
| Product morphology | Numeric | `product_volume_cm3`, `product_density_g_cm3`, `product_max_dimension_cm`, `product_min_dimension_cm`, `product_dimension_ratio`, `freight_to_price_ratio`, `freight_per_kg`, `photos_per_100_currency` |
| Product morphology | Binary | `product_dimensions_missing_flag`, `product_weight_missing_flag`, `product_photos_missing_flag`, `product_price_zero_flag`, `product_weight_zero_flag` |
| Product content completeness | Numeric | `product_name_length`, `product_description_length`, `product_metadata_missing_count` |
| Product content completeness | Binary | `product_content_missing_flag` |

Schema version is `p5-item-v11-interactions`.

## 6. Runtime environment

- Python requirement >=3.11 (Black target Python 3.11).
- Recorded packages: CatBoost 1.2.10; joblib 1.6.0; NumPy 2.4.6; pandas 2.3.3; PyArrow 21.0.0; scikit-learn 1.9.1.
- GPU was used only by the bounded CatBoost challenger (`task_type=GPU`, `devices=0`). The retained Random Forest is CPU-based.
- Recorded Git commit: `6e8976f8f5a91e9efa4c2c135aa5ea9a80385f05`; report records a dirty working tree.

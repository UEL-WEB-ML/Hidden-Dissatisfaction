# Olist data contract

## Expected raw files

Store the following files under `data/raw/olist/`:

```text
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
```

Raw files are immutable local inputs and must not be committed.

## Canonical grains

The ML modeling table has exactly one row per product item, keyed by `(order_id, order_item_id)` and exposed as `product_item_id = order_id + '-' + order_item_id`. The operational queue has exactly one row per `order_id` and is derived from item predictions using the versioned aggregation rule `max-v1`.

Order-level tables such as payments and reviews must be aggregated to one row per order before being joined to product items. Item and product attributes remain at item grain. Every item in the same order inherits the same observed order-review label; this weak label does not identify the item responsible for the review. All items from an order must remain in the same temporal split.

Minimum checks:

- required columns exist;
- declared keys have expected uniqueness;
- timestamps parse without silent coercion;
- order/payment aggregates do not multiply product-item rows;
- `(order_id, order_item_id)` and `product_item_id` are unique and stable;
- review multiplicity is reported and resolved by an explicit versioned policy;
- delivered and estimated timestamps exist for the primary population;
- review score is in the range 1–5 when observed;
- target and forbidden review fields are absent from the feature matrix;
- every order's items belong to exactly one temporal partition;
- order-level predictions reproduce `max-v1` from their item predictions.

## Dataset zones

- `raw`: untouched source CSV files.
- `interim`: deterministic validated/aggregated tables.
- `processed`: split-ready product-item feature/label datasets with schema metadata.

Each generated dataset should be accompanied by a manifest containing source hashes, row count, column schema, creation code version, and feature cutoff policy.

## Decision status and remaining research limits

The operational modelling decisions that gate the current product-item pipeline
are resolved and versioned:

1. Multiple reviews use the latest answered review with deterministic
   tie-breaks (ADR-001).
2. A review created at the same timestamp as delivery is excluded; the primary
   cohort requires `review_creation_date > prediction_at` (ADR-008).
3. Olist does not provide an item-level delivery timestamp. Split delivery is
   therefore not asserted as an observed fact; item and seller counts are only
   non-causal proxies.
4. Legacy historical mean-review features require both strict event-time
   cutoffs and at least five prior observations; otherwise they are null with a
   low-support flag (ADR-008).
5. Schema `p5-item-v3-target-history` adds Bayesian negative-review history.
   An historical order contributes only when both its delivery prediction event
   and its review creation event are strictly earlier than the current
   `prediction_at`. Order/entity events are deduplicated before aggregation.
   Seller, category, and seller-category rates use prior strength `25`, expose
   their support, and fall back to the expanding global prior. Before any label
   exists globally, that prior is the neutral value `0.5`. The 30/90-day windows
   are inclusive at their lower time boundary and strict at `prediction_at`.

Olist reviews remain order-level weak labels. A future item-specific label is
research outside the current dataset contract, not a prerequisite for this
release. It would require a new data contract and evaluation protocol before it
could replace the inherited label.

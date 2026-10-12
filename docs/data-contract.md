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

## Canonical grain

The modeling table has exactly one row per `order_id`. Every one-to-many table must be aggregated to order grain before joining. A join that changes the expected order count must fail loudly.

Minimum checks:

- required columns exist;
- declared keys have expected uniqueness;
- timestamps parse without silent coercion;
- order-item/payment aggregates do not duplicate orders;
- review multiplicity is reported and resolved by an explicit versioned policy;
- delivered and estimated timestamps exist for the primary population;
- review score is in the range 1–5 when observed;
- target and forbidden review fields are absent from the feature matrix.

## Dataset zones

- `raw`: untouched source CSV files.
- `interim`: deterministic validated/aggregated tables.
- `processed`: split-ready feature/label datasets with schema metadata.

Each generated dataset should be accompanied by a manifest containing source hashes, row count, column schema, creation code version, and feature cutoff policy.

## Unresolved contract decisions

Resolve and record these before producing final results:

1. How multiple reviews for one order map to one order-level label.
2. Whether same-timestamp delivery/review observations provide a meaningful intervention window.
3. Whether split delivery can be observed directly or only proxied by item/seller counts.
4. Which historical seller/category aggregates have sufficient prior support.

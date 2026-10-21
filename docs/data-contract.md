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

## Unresolved contract decisions

Resolve and record these before producing final results:

1. How multiple reviews for one order map to the shared label inherited by its product items.
2. Whether same-timestamp delivery/review observations provide a meaningful intervention window.
3. Whether split delivery can be observed directly or only proxied by item/seller counts.
4. Which historical seller/category aggregates have sufficient prior support.
5. Whether a future item-specific label can replace the inherited order-review label.

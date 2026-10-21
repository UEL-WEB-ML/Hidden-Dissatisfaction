---
title: "Olist dataset schema notes"
retrieved: 2026-09-26
source: "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
status: "Kaggle page title verified; schema must be confirmed against downloaded CSV files"
---

# Olist Brazilian E-Commerce dataset

The public dataset is distributed as multiple relational CSV files. The project should treat the downloaded files as the final source of truth for columns, types, ranges and missingness rather than relying only on online descriptions.

## Expected tables used by this project

- `olist_orders_dataset.csv`: order lifecycle and timestamps, including purchase, approval, carrier handoff, customer delivery and estimated delivery.
- `olist_order_items_dataset.csv`: one-to-many rows for products and sellers inside each order, with item price and freight value.
- `olist_order_payments_dataset.csv`: one-to-many payment methods and installments per order.
- `olist_order_reviews_dataset.csv`: review score and review timestamps; review text must not be used as a predictive feature.
- `olist_customers_dataset.csv`: order-level customer key, stable customer key and approximate location.
- `olist_sellers_dataset.csv`: seller location.
- `olist_products_dataset.csv`: product category and physical or description attributes.
- `olist_geolocation_dataset.csv`: ZIP-prefix coordinates; rows are not unique per ZIP prefix and require aggregation before joining.
- `product_category_name_translation.csv`: category translation lookup.

## Join and grain risks to verify from the files

- Joining orders directly to items, payments and reviews can multiply rows. Aggregate each one-to-many table to one row per `order_id` before the final join.
- Confirm whether an order can have duplicate or multiple review records; define a deterministic rule and record how many rows are affected.
- `customer_id` identifies the customer record for an order, whereas `customer_unique_id` is intended for cross-order customer history. Historical customer features must use only prior orders.
- Product, seller and customer history features must be computed with a point-in-time condition, not with whole-dataset aggregates.
- Coordinates and ZIP prefixes are approximate. Distance is a proxy, not a precise traveled route.
- All timestamps require parsing and chronological consistency checks. Missing delivery timestamps are expected for undelivered orders and should be filtered according to the study population.

## Required local verification

Before feature engineering, create a data profile that records file hashes, row counts, key uniqueness, null rates, date ranges, foreign-key coverage and one-to-many multiplicities. Do not present online row counts as final thesis results; reproduce them from the exact local dataset version.

{{ config(materialized='table', schema='gold') }}

select c.product_item_id, c.source_run_id, c.order_id, c.order_item_id,
       c.product_id, c.seller_id, c.product_category, c.customer_id,
       c.prediction_at, c.prediction_at as delivered_customer_date,
       c.order_purchase_timestamp, c.order_delivered_carrier_date,
       c.order_estimated_delivery_date, c.price, c.freight_value,
       c.item_plus_freight_amount, c.payment_count, c.payment_amount,
       c.max_payment_installments, c.order_weight,
       c.canonical_review_score, c.negative_label as negative,
       c.review_created_at, c.review_id, c.review_count as review_multiplicity,
       'adr-001-latest-answer-v1' as review_resolution,
       'adr-001-latest-answered-v1' as review_policy_version, c.cohort_version,
       h.history_version, 'ml-modelling-items-v1' as feature_schema_version,
       c.customer_city, c.customer_state, c.zip_code_prefix,
       c.on_time_flag, (c.customer_state is null)::int as geography_missing_flag,
       (c.order_delivered_carrier_date is null)::int as carrier_delivery_missing_flag,
       h.seller_prior_review_count, h.seller_prior_review_score_avg,
       h.seller_history_low_support_flag, h.category_prior_review_count,
       h.category_prior_review_score_avg, h.category_history_low_support_flag,
       'p4' as feature_set_version, 'review-window-v1' as observation_window_version
from (select c0.*, 1.0 / nullif(count(*) over (partition by source_run_id, order_id), 0) as order_weight
      from {{ ref('int_p4_cohort') }} c0) c
join {{ ref('int_p4_history') }} h using (source_run_id, product_item_id)

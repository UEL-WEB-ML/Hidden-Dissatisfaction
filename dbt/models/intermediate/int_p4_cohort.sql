{{ config(
    materialized='table',
    schema='intermediate',
    indexes=[
      {'columns': ['source_run_id', 'product_item_id'], 'unique': true},
      {'columns': ['source_run_id', 'seller_id', 'prediction_at']},
      {'columns': ['source_run_id', 'product_category', 'prediction_at']},
      {'columns': ['source_run_id', 'order_id', 'prediction_at']}
    ]
) }}

with base as (
 select i.*, o.customer_id, o.order_status, o.order_purchase_timestamp,
        o.order_delivered_customer_date as prediction_at,
        o.order_estimated_delivery_date, o.order_delivered_carrier_date,
        r.review_score, r.review_creation_date as review_created_at,
        r.review_id, r.review_count, p.payment_count, p.payment_amount,
        p.max_payment_installments, pr.category as product_category,
        pr.product_photos_qty, pr.product_weight_g, pr.product_length_cm,
        pr.product_height_cm, pr.product_width_cm,
        cu.customer_city, cu.customer_state, cu.zip_code_prefix
 from {{ ref('int_p4_item_base') }} i
 join {{ ref('stg_orders') }} o using (source_run_id, order_id)
 left join {{ ref('int_p4_review_canonical') }} r using (source_run_id, order_id)
 left join {{ ref('int_p4_payment_features') }} p using (source_run_id, order_id)
 left join {{ ref('dim_product') }} pr using (source_run_id, product_id)
 left join {{ ref('dim_customer') }} cu using (source_run_id, customer_id)
)
select *, order_id || '-' || order_item_id as product_item_id,
       extract(epoch from (order_estimated_delivery_date - prediction_at)) / 86400.0 as estimated_delivery_buffer_days,
       extract(epoch from (prediction_at - order_purchase_timestamp)) / 86400.0 as purchase_to_delivery_days,
       extract(epoch from (prediction_at - order_delivered_carrier_date)) / 86400.0 as carrier_to_delivery_days,
       review_score as canonical_review_score,
       (review_score in (1,2))::int as negative_label,
       case when review_score is not null and review_created_at > prediction_at
            then 1 else 0 end as primary_cohort_flag,
       (prediction_at <= order_estimated_delivery_date)::int as on_time_flag,
       'adr-001-latest-answer-v1' as review_policy_version,
       'p4-primary-cohort-v1' as cohort_version
from base
where prediction_at is not null
  and order_estimated_delivery_date is not null
  and prediction_at <= order_estimated_delivery_date
  and review_score is not null
  and review_created_at > prediction_at

{{ config(materialized='table', schema='intermediate') }}

with base as (
 select i.*, o.customer_id, o.order_status, o.order_purchase_timestamp,
        o.order_delivered_customer_date as prediction_at,
        o.order_estimated_delivery_date, o.order_delivered_carrier_date,
        r.review_score, r.review_creation_date as review_created_at,
        r.review_id, r.review_count, p.payment_count, p.payment_amount,
        p.max_payment_installments, pr.category as product_category,
        cu.customer_city, cu.customer_state, cu.zip_code_prefix
 from {{ ref('int_p4_item_base') }} i
 join {{ ref('stg_orders') }} o using (source_run_id, order_id)
 left join {{ ref('int_p4_review_canonical') }} r using (source_run_id, order_id)
 left join {{ ref('int_p4_payment_features') }} p using (source_run_id, order_id)
 left join {{ ref('dim_product') }} pr using (source_run_id, product_id)
 left join {{ ref('dim_customer') }} cu using (source_run_id, customer_id)
)
select *, order_id || '-' || order_item_id as product_item_id,
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

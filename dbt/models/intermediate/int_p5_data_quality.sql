{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

-- Missingness is retained as an observed data-quality state, never imputed as
-- a physical value.  Product morphology/content indicators already live in S6;
-- this model adds the remaining order/customer/category/payment indicators.
with payment_orders as (
    select distinct source_run_id, order_id from {{ ref('stg_order_payments') }}
)
select c.source_run_id, c.product_item_id,
       (c.product_category is null or c.product_category = '(missing)')::int as category_missing_flag,
       (p.order_id is null)::int as payment_missing_flag,
       (c.customer_state is null)::int as customer_state_missing_flag,
       (c.order_delivered_carrier_date is null)::int as data_quality_carrier_delivery_missing_flag,
       ((c.product_category is null or c.product_category = '(missing)')::int
        + (p.order_id is null)::int + (c.customer_state is null)::int
        + (c.order_delivered_carrier_date is null)::int)::int as item_data_quality_missing_count,
       'p5-data-quality-v1' as data_quality_version
from {{ ref('int_p4_cohort') }} c
left join payment_orders p using (source_run_id, order_id)

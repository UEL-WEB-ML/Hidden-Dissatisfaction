{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

-- Limited, hypothesis-led interactions. Each input belongs to a feature group
-- that passed an earlier ablation; null propagates when a source measurement is
-- unavailable rather than fabricating a ratio.
select c.source_run_id, c.product_item_id,
       oc.order_seller_count * oc.order_category_count as order_seller_category_complexity,
       c.estimated_delivery_buffer_days / nullif(c.purchase_to_delivery_days, 0) as delivery_buffer_to_duration_ratio,
       so.seller_mean_purchase_to_delivery_days * pm.freight_to_price_ratio as seller_speed_x_freight_ratio,
       pm.product_density_g_cm3 * (c.item_plus_freight_amount / nullif(oc.order_item_value_total, 0)) as density_x_item_value_share,
       (c.purchase_to_delivery_days = 0)::int as purchase_delivery_zero_flag,
       'p5-interactions-v1' as interactions_version
from {{ ref('int_p4_cohort') }} c
join {{ ref('int_p5_order_composition') }} oc using (source_run_id, product_item_id)
join {{ ref('int_p5_seller_operations') }} so using (source_run_id, product_item_id)
join {{ ref('int_p5_product_morphology') }} pm using (source_run_id, product_item_id)

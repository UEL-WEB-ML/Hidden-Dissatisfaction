with features as (
    select source_run_id, order_id,
           count(distinct order_seller_count) as seller_count_values,
           count(distinct order_category_count) as category_count_values,
           count(distinct order_product_count) as product_count_values,
           count(distinct order_unique_product_count) as unique_product_count_values,
           count(distinct order_item_count) as item_count_values,
           count(distinct order_item_value_total) as total_values,
           count(distinct order_freight_total) as freight_total_values,
           count(distinct order_freight_share) as freight_share_values,
           count(distinct order_max_item_value_share) as max_share_values,
           count(distinct order_min_item_value_share) as min_share_values,
           count(distinct order_category_hhi) as category_hhi_values,
           count(distinct order_seller_hhi) as seller_hhi_values
    from {{ ref('int_p5_order_composition') }}
    join {{ ref('int_p4_cohort') }} using (source_run_id, product_item_id)
    group by source_run_id, order_id
)
select *
from features
where seller_count_values > 1 or category_count_values > 1 or product_count_values > 1
   or unique_product_count_values > 1 or item_count_values > 1 or total_values > 1
   or freight_total_values > 1 or freight_share_values > 1 or max_share_values > 1
   or min_share_values > 1 or category_hhi_values > 1 or seller_hhi_values > 1

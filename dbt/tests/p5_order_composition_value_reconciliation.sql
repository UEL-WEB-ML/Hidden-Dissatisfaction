with item_values as (
    select source_run_id, order_id,
           item_plus_freight_amount / nullif(sum(item_plus_freight_amount) over (partition by source_run_id, order_id), 0) as item_value_share
    from {{ ref('int_p4_cohort') }}
), composition_orders as (
    select distinct o.source_run_id, c.order_id, o.order_item_value_total
    from {{ ref('int_p5_order_composition') }} o
    join {{ ref('int_p4_cohort') }} c using (source_run_id, product_item_id)
), checks as (
    select i.source_run_id, i.order_id, sum(i.item_value_share) as share_sum,
           o.order_item_value_total
    from item_values i
    join composition_orders o using (source_run_id, order_id)
    group by i.source_run_id, i.order_id, o.order_item_value_total
)
select * from checks
where order_item_value_total > 0 and abs(share_sum - 1) > 0.000001

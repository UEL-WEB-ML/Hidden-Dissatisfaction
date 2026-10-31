with features as (
    select p.source_run_id, c.order_id, count(distinct p.payment_type_count) as type_count_values,
           count(distinct p.payment_to_order_value_ratio) as ratio_values,
           count(distinct p.payment_type_hhi) as hhi_values,
           count(distinct p.primary_payment_type) as primary_type_values,
           count(distinct p.split_payment_flag) as split_flag_values
    from {{ ref('int_p5_payment_behavior') }} p
    join {{ ref('int_p4_cohort') }} c using (source_run_id, product_item_id)
    group by p.source_run_id, c.order_id
)
select * from features where type_count_values > 1 or ratio_values > 1 or hhi_values > 1
   or primary_type_values > 1 or split_flag_values > 1

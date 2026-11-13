{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

-- All values here belong to the current order and are therefore known at its
-- prediction cutoff.  The explicit missing-category bucket prevents a null
-- category from silently disappearing from order complexity/concentration.
with items as (
    select source_run_id, product_item_id, order_id, seller_id, product_id,
           coalesce(product_category, '(missing)') as category_bucket,
           price, freight_value, item_plus_freight_amount
    from {{ ref('int_p4_cohort') }}
), order_totals as (
    select source_run_id, order_id,
           count(*)::int as order_item_count,
           count(seller_id)::int as order_seller_count,
           count(distinct category_bucket)::int as order_category_count,
           count(product_id)::int as order_product_count,
           count(distinct product_id)::int as order_unique_product_count,
           sum(item_plus_freight_amount) as order_item_value_total,
           sum(freight_value) as order_freight_total,
           avg(price) as order_price_mean,
           stddev_samp(price) as order_price_std,
           max(price) as order_price_max,
           min(price) as order_price_min,
           avg(freight_value) as order_freight_mean,
           stddev_samp(freight_value) as order_freight_std,
           max(freight_value) as order_freight_max,
           max(item_plus_freight_amount) as order_max_item_value,
           min(item_plus_freight_amount) as order_min_item_value
    from items
    group by source_run_id, order_id
), category_values as (
    select source_run_id, order_id, category_bucket,
           sum(item_plus_freight_amount) as category_value
    from items
    group by source_run_id, order_id, category_bucket
), seller_values as (
    select source_run_id, order_id, seller_id,
           sum(item_plus_freight_amount) as seller_value
    from items
    group by source_run_id, order_id, seller_id
), category_hhi as (
    select v.source_run_id, v.order_id,
           sum(power(v.category_value / nullif(t.order_item_value_total, 0), 2)) as order_category_hhi
    from category_values v
    join order_totals t using (source_run_id, order_id)
    group by v.source_run_id, v.order_id
), seller_hhi as (
    select v.source_run_id, v.order_id,
           sum(power(v.seller_value / nullif(t.order_item_value_total, 0), 2)) as order_seller_hhi
    from seller_values v
    join order_totals t using (source_run_id, order_id)
    group by v.source_run_id, v.order_id
), order_features as (
    select t.*,
           t.order_freight_total / nullif(t.order_item_value_total, 0) as order_freight_share,
           t.order_max_item_value / nullif(t.order_item_value_total, 0) as order_max_item_value_share,
           t.order_min_item_value / nullif(t.order_item_value_total, 0) as order_min_item_value_share,
           ch.order_category_hhi, sh.order_seller_hhi,
           (t.order_item_count > 1)::int as multi_item_flag,
           (t.order_seller_count > 1)::int as multi_seller_flag,
           (t.order_category_count > 1)::int as multi_category_flag
    from order_totals t
    join category_hhi ch using (source_run_id, order_id)
    join seller_hhi sh using (source_run_id, order_id)
)
select i.source_run_id, i.product_item_id,
       f.order_seller_count, f.order_category_count, f.order_product_count,
       f.order_unique_product_count, f.order_item_count, f.order_item_value_total,
       f.order_freight_total, f.order_freight_share, f.order_max_item_value_share,
       f.order_min_item_value_share, f.order_price_mean, f.order_price_std,
       f.order_price_max, f.order_price_min, f.order_freight_mean,
       f.order_freight_std, f.order_freight_max, f.order_category_hhi,
       f.order_seller_hhi, f.multi_item_flag, f.multi_seller_flag,
       f.multi_category_flag, 'p5-order-composition-v1' as order_composition_version
from items i
join order_features f using (source_run_id, order_id)

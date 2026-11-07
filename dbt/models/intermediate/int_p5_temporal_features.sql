{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

-- Daily timelines use the wider delivered-order population and exclude the
-- cutoff day itself. Thus no current/same-day delivery can contribute to a
-- recency feature, and no review-derived fields are used.
with delivered_orders as (
    select source_run_id, order_id, order_delivered_customer_date::date as event_day
    from {{ ref('stg_orders') }}
    where order_status = 'delivered' and order_delivered_customer_date is not null
), seller_events as (
    select distinct i.source_run_id, i.order_id, i.seller_id, o.event_day
    from {{ ref('stg_order_items') }} i join delivered_orders o using (source_run_id, order_id)
), category_events as (
    select distinct i.source_run_id, i.order_id, coalesce(p.category, '(missing)') as category, o.event_day
    from {{ ref('stg_order_items') }} i join delivered_orders o using (source_run_id, order_id)
    left join {{ ref('stg_products') }} p using (source_run_id, product_id)
), event_rows as (
    select source_run_id, 'global'::text as entity_type, '*'::text as entity_key, event_day, count(*)::int as event_count
    from delivered_orders group by source_run_id, event_day
    union all
    select source_run_id, 'seller', seller_id, event_day, count(*)::int
    from seller_events group by source_run_id, seller_id, event_day
    union all
    select source_run_id, 'category', category, event_day, count(*)::int
    from category_events group by source_run_id, category, event_day
), query_rows as (
    select source_run_id, product_item_id, 'global'::text as entity_type, '*'::text as entity_key, prediction_at::date as event_day
    from {{ ref('int_p4_cohort') }}
    union all
    select source_run_id, product_item_id, 'seller', seller_id, prediction_at::date
    from {{ ref('int_p4_cohort') }}
    union all
    select source_run_id, product_item_id, 'category', coalesce(product_category, '(missing)'), prediction_at::date
    from {{ ref('int_p4_cohort') }}
), timeline_days as (
    select source_run_id, entity_type, entity_key, event_day, sum(event_count)::int as event_count
    from (
        select source_run_id, entity_type, entity_key, event_day, event_count from event_rows
        union all
        select source_run_id, entity_type, entity_key, event_day, 0::int from query_rows
    ) x
    group by source_run_id, entity_type, entity_key, event_day
), rolling as (
    select *,
           coalesce(sum(event_count) over (
               partition by source_run_id, entity_type, entity_key order by event_day
               range between interval '7 days' preceding and interval '1 day' preceding
           ), 0)::int as prior_volume_7d,
           coalesce(sum(event_count) over (
               partition by source_run_id, entity_type, entity_key order by event_day
               range between interval '30 days' preceding and interval '1 day' preceding
           ), 0)::int as prior_volume_30d
    from timeline_days
), query_features as (
    select q.source_run_id, q.product_item_id, q.entity_type, r.prior_volume_7d, r.prior_volume_30d
    from query_rows q join rolling r using (source_run_id, entity_type, entity_key, event_day)
), pivoted as (
    select source_run_id, product_item_id,
           max(prior_volume_7d) filter (where entity_type = 'global') as global_order_volume_7d,
           max(prior_volume_30d) filter (where entity_type = 'global') as global_order_volume_30d,
           max(prior_volume_7d) filter (where entity_type = 'seller') as seller_recent_order_volume_7d,
           max(prior_volume_30d) filter (where entity_type = 'seller') as seller_recent_order_volume_30d,
           max(prior_volume_7d) filter (where entity_type = 'category') as category_recent_order_volume_7d,
           max(prior_volume_30d) filter (where entity_type = 'category') as category_recent_order_volume_30d
    from query_features group by source_run_id, product_item_id
), first_event as (
    select source_run_id, min(event_day) as first_event_day from delivered_orders group by source_run_id
)
select c.source_run_id, c.product_item_id,
       extract(month from c.order_purchase_timestamp)::int as purchase_month,
       extract(isodow from c.order_purchase_timestamp)::int as purchase_weekday,
       extract(hour from c.order_purchase_timestamp)::int as purchase_hour,
       extract(month from c.prediction_at)::int as delivery_month,
       extract(isodow from c.prediction_at)::int as delivery_weekday,
       (c.prediction_at::date - f.first_event_day)::int as delivery_dataset_age_days,
       p.global_order_volume_7d, p.global_order_volume_30d,
       p.seller_recent_order_volume_7d, p.seller_recent_order_volume_30d,
       p.category_recent_order_volume_7d, p.category_recent_order_volume_30d,
       p.category_recent_order_volume_7d / 7.0 - p.category_recent_order_volume_30d / 30.0 as category_recent_volume_delta,
       'p5-temporal-features-v1' as temporal_features_version
from {{ ref('int_p4_cohort') }} c
join pivoted p using (source_run_id, product_item_id)
join first_event f using (source_run_id)

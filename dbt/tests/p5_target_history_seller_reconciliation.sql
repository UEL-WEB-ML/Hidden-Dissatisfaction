with all_items as (
    select *
    from {{ ref('int_p4_cohort') }}
),
current_items as (
    select * from all_items
    where mod(hashtextextended(product_item_id, 0), 211) = 0
),
seller_events as (
    select source_run_id, order_id, seller_id,
           min(prediction_at) as prediction_at,
           min(review_created_at) as review_created_at,
           max(negative_label) as negative
    from all_items
    group by source_run_id, order_id, seller_id
),
expected as (
    select c.source_run_id, c.product_item_id,
           count(h.order_id)::int as history_count,
           coalesce(sum(h.negative), 0)::int as negative_count,
           count(h.order_id) filter (
               where h.prediction_at >= c.prediction_at - interval '30 days'
           )::int as history_count_30d,
           count(h.order_id) filter (
               where h.prediction_at >= c.prediction_at - interval '90 days'
           )::int as history_count_90d
    from current_items c
    left join seller_events h
      on h.source_run_id = c.source_run_id
     and h.seller_id = c.seller_id
     and h.prediction_at < c.prediction_at
     and h.review_created_at < c.prediction_at
     and h.order_id <> c.order_id
    group by c.source_run_id, c.product_item_id
)
select a.source_run_id, a.product_item_id
from {{ ref('int_p5_target_history') }} a
join expected e using (source_run_id, product_item_id)
where a.seller_negative_history_count <> e.history_count
   or a.seller_negative_history_negative_count <> e.negative_count
   or a.seller_negative_history_count_30d <> e.history_count_30d
   or a.seller_negative_history_count_90d <> e.history_count_90d

{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}
{% set prior_strength = var('target_history_prior_strength', 25) %}

with current_items as (select * from {{ ref('int_p4_cohort') }}),
order_events as (
 select source_run_id, order_id, min(prediction_at) prediction_at,
        min(review_created_at) review_created_at, max(negative_label)::int negative,
        avg(review_score)::numeric review_score
 from current_items group by source_run_id, order_id
), seller_events as (
 select source_run_id, order_id, seller_id, min(prediction_at) prediction_at,
        min(review_created_at) review_created_at, max(negative_label)::int negative,
        avg(review_score)::numeric review_score
 from current_items group by source_run_id, order_id, seller_id
), category_events as (
 select source_run_id, order_id, coalesce(product_category, '(missing)') entity_key,
        min(prediction_at) prediction_at, min(review_created_at) review_created_at,
        max(negative_label)::int negative, avg(review_score)::numeric review_score
 from current_items group by source_run_id, order_id, coalesce(product_category, '(missing)')
), seller_category_events as (
 select source_run_id, order_id, seller_id, coalesce(product_category, '(missing)') secondary_key,
        min(prediction_at) prediction_at, min(review_created_at) review_created_at,
        max(negative_label)::int negative, avg(review_score)::numeric review_score
 from current_items group by source_run_id, order_id, seller_id, coalesce(product_category, '(missing)')
), entity_events as (
 select source_run_id, order_id, 'global'::text entity_type, '*'::text entity_key,
        ''::text secondary_key, prediction_at, greatest(prediction_at, review_created_at) available_at,
        negative, review_score from order_events
 union all select source_run_id, order_id, 'seller', seller_id, '', prediction_at,
        greatest(prediction_at, review_created_at), negative, review_score from seller_events
 union all select source_run_id, order_id, 'category', entity_key, '', prediction_at,
        greatest(prediction_at, review_created_at), negative, review_score from category_events
 union all select source_run_id, order_id, 'seller_category', seller_id, secondary_key, prediction_at,
        greatest(prediction_at, review_created_at), negative, review_score from seller_category_events
), query_points as (
 select source_run_id, product_item_id, prediction_at timeline_at, 0::int point_kind,
        entity_type, entity_key, secondary_key, 0::int count_delta, 0::int negative_delta,
        0::numeric score_delta, 0::int count_30d_delta, 0::int negative_30d_delta,
        0::numeric score_30d_delta, 0::int count_90d_delta, 0::int negative_90d_delta,
        0::numeric score_90d_delta
 from current_items cross join lateral (values
   ('global'::text, '*'::text, ''::text), ('seller', seller_id, ''),
   ('category', coalesce(product_category, '(missing)'), ''),
   ('seller_category', seller_id, coalesce(product_category, '(missing)'))
 ) entity(entity_type, entity_key, secondary_key)
), availability_points as (
 select source_run_id, null::text product_item_id, available_at timeline_at, 1::int point_kind,
        entity_type, entity_key, secondary_key, 1::int count_delta, negative negative_delta,
        review_score score_delta,
        (available_at < prediction_at + interval '30 days')::int count_30d_delta,
        negative * (available_at < prediction_at + interval '30 days')::int negative_30d_delta,
        review_score * (available_at < prediction_at + interval '30 days')::int score_30d_delta,
        (available_at < prediction_at + interval '90 days')::int count_90d_delta,
        negative * (available_at < prediction_at + interval '90 days')::int negative_90d_delta,
        review_score * (available_at < prediction_at + interval '90 days')::int score_90d_delta
 from entity_events
), expiration_points as (
 select source_run_id, null::text product_item_id, prediction_at + window_size timeline_at,
        1::int point_kind, entity_type, entity_key, secondary_key,
        0::int count_delta, 0::int negative_delta, 0::numeric score_delta,
        (case when window_size = interval '30 days' then -1 else 0 end)
          * (available_at < prediction_at + window_size)::int count_30d_delta,
        (case when window_size = interval '30 days' then -negative else 0 end)
          * (available_at < prediction_at + window_size)::int negative_30d_delta,
        (case when window_size = interval '30 days' then -review_score else 0 end)
          * (available_at < prediction_at + window_size)::int score_30d_delta,
        (case when window_size = interval '90 days' then -1 else 0 end)
          * (available_at < prediction_at + window_size)::int count_90d_delta,
        (case when window_size = interval '90 days' then -negative else 0 end)
          * (available_at < prediction_at + window_size)::int negative_90d_delta,
        (case when window_size = interval '90 days' then -review_score else 0 end)
          * (available_at < prediction_at + window_size)::int score_90d_delta
 from entity_events cross join (values (interval '30 days'), (interval '90 days')) w(window_size)
), timeline as (
 select * from query_points union all select * from availability_points union all select * from expiration_points
), cumulative as (
 select *, sum(count_delta) over h history_count, sum(negative_delta) over h negative_count,
        sum(score_delta) over h score_sum, sum(count_30d_delta) over h history_count_30d,
        sum(negative_30d_delta) over h negative_count_30d, sum(score_30d_delta) over h score_sum_30d,
        sum(count_90d_delta) over h history_count_90d, sum(negative_90d_delta) over h negative_count_90d,
        sum(score_90d_delta) over h score_sum_90d
 from timeline window h as (partition by source_run_id, entity_type, entity_key, secondary_key
   order by timeline_at, point_kind rows between unbounded preceding and current row)
), item_history as (
 select source_run_id, product_item_id,
  max(history_count) filter(where entity_type='global')::int global_count,
  max(negative_count) filter(where entity_type='global')::int global_negative,
  max(history_count_30d) filter(where entity_type='global')::int global_count_30d,
  max(negative_count_30d) filter(where entity_type='global')::int global_negative_30d,
  max(history_count_90d) filter(where entity_type='global')::int global_count_90d,
  max(negative_count_90d) filter(where entity_type='global')::int global_negative_90d,
  max(history_count) filter(where entity_type='seller')::int seller_count,
  max(negative_count) filter(where entity_type='seller')::int seller_negative,
  max(score_sum) filter(where entity_type='seller') seller_score_sum,
  max(history_count_30d) filter(where entity_type='seller')::int seller_count_30d,
  max(negative_count_30d) filter(where entity_type='seller')::int seller_negative_30d,
  max(score_sum_30d) filter(where entity_type='seller') seller_score_sum_30d,
  max(history_count_90d) filter(where entity_type='seller')::int seller_count_90d,
  max(negative_count_90d) filter(where entity_type='seller')::int seller_negative_90d,
  max(score_sum_90d) filter(where entity_type='seller') seller_score_sum_90d,
  max(history_count) filter(where entity_type='category')::int category_count,
  max(negative_count) filter(where entity_type='category')::int category_negative,
  max(history_count_30d) filter(where entity_type='category')::int category_count_30d,
  max(negative_count_30d) filter(where entity_type='category')::int category_negative_30d,
  max(history_count_90d) filter(where entity_type='category')::int category_count_90d,
  max(negative_count_90d) filter(where entity_type='category')::int category_negative_90d,
  max(history_count) filter(where entity_type='seller_category')::int seller_category_count,
  max(negative_count) filter(where entity_type='seller_category')::int seller_category_negative
 from cumulative where product_item_id is not null group by source_run_id, product_item_id
), p as (
 select *, case when global_count=0 then 0.5::numeric else global_negative::numeric/global_count end global_rate,
  case when global_count_30d=0 then case when global_count=0 then 0.5::numeric else global_negative::numeric/global_count end
       else global_negative_30d::numeric/global_count_30d end global_rate_30d,
  case when global_count_90d=0 then case when global_count=0 then 0.5::numeric else global_negative::numeric/global_count end
       else global_negative_90d::numeric/global_count_90d end global_rate_90d
 from item_history
)
select source_run_id, product_item_id, global_count global_prior_order_count,
 global_negative global_prior_negative_count, global_rate global_prior_negative_rate,
 global_count_30d global_prior_order_count_30d, global_rate_30d global_prior_negative_rate_30d,
 global_count_90d global_prior_order_count_90d, global_rate_90d global_prior_negative_rate_90d,
 seller_count seller_negative_history_count, seller_negative seller_negative_history_negative_count,
 ln(1+seller_count) seller_negative_history_support_log1p, (seller_count=0)::int seller_negative_history_cold_start_flag,
 (seller_count between 1 and 4)::int seller_negative_history_low_support_flag,
 (seller_negative+{{ prior_strength }}*global_rate)/(seller_count+{{ prior_strength }}) seller_smoothed_negative_rate,
 seller_score_sum/nullif(seller_count,0) seller_negative_history_score_mean,
 seller_count_30d seller_negative_history_count_30d,
 (seller_negative_30d+{{ prior_strength }}*global_rate_30d)/(seller_count_30d+{{ prior_strength }}) seller_smoothed_negative_rate_30d,
 seller_score_sum_30d/nullif(seller_count_30d,0) seller_negative_history_score_mean_30d,
 seller_count_90d seller_negative_history_count_90d,
 (seller_negative_90d+{{ prior_strength }}*global_rate_90d)/(seller_count_90d+{{ prior_strength }}) seller_smoothed_negative_rate_90d,
 seller_score_sum_90d/nullif(seller_count_90d,0) seller_negative_history_score_mean_90d,
 category_count category_negative_history_count, category_negative category_negative_history_negative_count,
 ln(1+category_count) category_negative_history_support_log1p, (category_count=0)::int category_negative_history_cold_start_flag,
 (category_count between 1 and 4)::int category_negative_history_low_support_flag,
 (category_negative+{{ prior_strength }}*global_rate)/(category_count+{{ prior_strength }}) category_smoothed_negative_rate,
 category_count_30d category_negative_history_count_30d,
 (category_negative_30d+{{ prior_strength }}*global_rate_30d)/(category_count_30d+{{ prior_strength }}) category_smoothed_negative_rate_30d,
 category_count_90d category_negative_history_count_90d,
 (category_negative_90d+{{ prior_strength }}*global_rate_90d)/(category_count_90d+{{ prior_strength }}) category_smoothed_negative_rate_90d,
 seller_category_count seller_category_negative_history_count,
 ln(1+seller_category_count) seller_category_negative_history_support_log1p,
 (seller_category_count=0)::int seller_category_negative_history_cold_start_flag,
 (seller_category_count between 1 and 4)::int seller_category_negative_history_low_support_flag,
 (seller_category_negative+{{ prior_strength }}*global_rate)/(seller_category_count+{{ prior_strength }}) seller_category_smoothed_negative_rate,
 {{ prior_strength }}::int target_history_prior_strength, 'p5-target-history-bayesian-v1' target_history_version
from p

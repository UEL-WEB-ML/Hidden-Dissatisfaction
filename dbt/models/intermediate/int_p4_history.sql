{{ config(materialized='table', schema='intermediate') }}
with current as (select * from {{ ref('int_p4_cohort') }}),
seller_events as (select source_run_id, order_id, seller_id, min(prediction_at) prediction_at, min(review_created_at) review_created_at, max(review_score) review_score from current group by source_run_id, order_id, seller_id),
category_events as (select source_run_id, order_id, product_category, min(prediction_at) prediction_at, min(review_created_at) review_created_at, max(review_score) review_score from current group by source_run_id, order_id, product_category),
seller_history as (
 select c.source_run_id, c.product_item_id, count(h.order_id)::int seller_prior_review_count, avg(h.review_score) seller_prior_review_score_avg
 from current c left join seller_events h on h.source_run_id=c.source_run_id and h.seller_id=c.seller_id and h.prediction_at<c.prediction_at and h.review_created_at<c.prediction_at and h.order_id<>c.order_id
 group by c.source_run_id, c.product_item_id
), category_history as (
 select c.source_run_id, c.product_item_id, count(h.order_id)::int category_prior_review_count, avg(h.review_score) category_prior_review_score_avg
 from current c left join category_events h on h.source_run_id=c.source_run_id and h.product_category=c.product_category and h.prediction_at<c.prediction_at and h.review_created_at<c.prediction_at and h.order_id<>c.order_id
 group by c.source_run_id, c.product_item_id
)
select c.product_item_id, c.source_run_id, s.seller_prior_review_count,
 case when s.seller_prior_review_count>=5 then s.seller_prior_review_score_avg end seller_prior_review_score_avg,
 (s.seller_prior_review_count<5)::int seller_history_low_support_flag, k.category_prior_review_count,
 case when k.category_prior_review_count>=5 then k.category_prior_review_score_avg end category_prior_review_score_avg,
 (k.category_prior_review_count<5)::int category_history_low_support_flag, 'p4-history-strict-prior-v1' history_version
from current c join seller_history s using(source_run_id,product_item_id) join category_history k using(source_run_id,product_item_id)

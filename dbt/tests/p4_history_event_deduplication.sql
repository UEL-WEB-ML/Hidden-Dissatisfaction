{{ config(tags=['slow', 'release_only']) }}

-- Exhaustive reconciliation retained for release/scheduled runs only.  The
-- deterministic P4 fixture is covered by p4_history_fixture_reconciliation.
with cohort as (
  select * from {{ ref('int_p4_cohort') }}
), seller_events as (
  select source_run_id, order_id, seller_id,
         min(prediction_at) as prediction_at,
         min(review_created_at) as review_created_at
  from cohort
  group by source_run_id, order_id, seller_id
), category_events as (
  select source_run_id, order_id, product_category,
         min(prediction_at) as prediction_at,
         min(review_created_at) as review_created_at
  from cohort
  group by source_run_id, order_id, product_category
), seller_expected as (
  select c.product_item_id, count(e.order_id)::int as expected_seller_count
  from cohort c
  left join seller_events e
    on e.seller_id = c.seller_id
   and e.prediction_at < c.prediction_at
   and e.review_created_at < c.prediction_at
   and e.order_id <> c.order_id
  group by c.product_item_id
), category_expected as (
  select c.product_item_id, count(e.order_id)::int as expected_category_count
  from cohort c
  left join category_events e
    on e.product_category = c.product_category
   and e.prediction_at < c.prediction_at
   and e.review_created_at < c.prediction_at
   and e.order_id <> c.order_id
  group by c.product_item_id
), expected as (
  select s.product_item_id, s.expected_seller_count,
         k.expected_category_count
  from seller_expected s
  join category_expected k using (product_item_id)
), actual as (
  select product_item_id, seller_prior_review_count,
         category_prior_review_count
  from {{ ref('ml_modelling_items') }}
)
select e.product_item_id, e.expected_seller_count, a.seller_prior_review_count,
       e.expected_category_count, a.category_prior_review_count
from expected e join actual a using (product_item_id)
where e.expected_seller_count <> a.seller_prior_review_count
   or e.expected_category_count <> a.category_prior_review_count

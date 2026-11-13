{{ config(tags=['p4_fast', 'invariant']) }}

-- An order can contain several canonical item contexts.  Seller and category
-- events therefore have independent grains; item-level columns must not make
-- either event look unstable.  Only the inputs consumed by the history
-- calculations are required to be single-valued at each event grain.
with cohort as (
    select source_run_id, order_id, seller_id, product_category,
           prediction_at, review_created_at, canonical_review_score
    from {{ ref('int_p4_cohort') }}
), seller_stability as (
    select source_run_id, order_id, seller_id,
           count(distinct prediction_at) as prediction_count,
           count(distinct review_created_at) as review_count,
           count(distinct canonical_review_score) as score_count
    from cohort
    group by source_run_id, order_id, seller_id
), category_stability as (
    select source_run_id, order_id, product_category,
           count(distinct prediction_at) as prediction_count,
           count(distinct review_created_at) as review_count,
           count(distinct canonical_review_score) as score_count
    from cohort
    group by source_run_id, order_id, product_category
)
select 'seller' as event_grain, source_run_id, order_id, seller_id as event_key
from seller_stability
where prediction_count <> 1 or review_count <> 1 or score_count <> 1
union all
select 'category' as event_grain, source_run_id, order_id, product_category as event_key
from category_stability
where prediction_count <> 1 or review_count <> 1 or score_count <> 1

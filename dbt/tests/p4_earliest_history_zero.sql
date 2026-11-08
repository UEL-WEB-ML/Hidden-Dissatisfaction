{{ config(tags=['p4_fast', 'invariant']) }}
with ranked as (
    select c.source_run_id, c.product_item_id, m.seller_prior_review_count,
           row_number() over (
             partition by c.source_run_id, c.seller_id
             order by c.prediction_at, c.product_item_id
           ) as rn
    from {{ ref('int_p4_cohort') }} c
    join {{ ref('ml_modelling_items') }} m using (source_run_id, product_item_id)
)
select product_item_id
from ranked
where rn = 1 and seller_prior_review_count <> 0

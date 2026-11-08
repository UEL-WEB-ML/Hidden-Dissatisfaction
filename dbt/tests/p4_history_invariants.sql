{{ config(tags=['p4_fast', 'invariant']) }}
select product_item_id
from {{ ref('ml_modelling_items') }}
where seller_prior_review_count < 0
   or category_prior_review_count < 0
   or (seller_prior_review_count < 5 and seller_prior_review_score_avg is not null)
   or (category_prior_review_count < 5 and category_prior_review_score_avg is not null)
   or (seller_prior_review_count >= 5 and seller_prior_review_score_avg is null)
   or (category_prior_review_count >= 5 and category_prior_review_score_avg is null)

select * from {{ ref('ml_modelling_items') }}
where (seller_prior_review_count < 5 and seller_prior_review_score_avg is not null)
   or (category_prior_review_count < 5 and category_prior_review_score_avg is not null)

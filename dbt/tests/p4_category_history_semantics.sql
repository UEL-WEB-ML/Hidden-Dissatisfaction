select * from {{ ref('ml_modelling_items') }}
where category_prior_review_count < 0
   or (category_prior_review_count < 5
       and category_prior_review_score_avg is not null)

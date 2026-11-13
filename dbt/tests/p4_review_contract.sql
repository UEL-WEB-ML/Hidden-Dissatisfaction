select * from {{ ref('ml_modelling_items') }}
where review_created_at <= prediction_at
   or canonical_review_score not between 1 and 5
   or negative not in (0, 1)

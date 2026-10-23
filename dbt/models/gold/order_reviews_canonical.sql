with ranked_reviews as (
  select
    r.*,
    count(*) over (partition by source_run_id, order_id)::int as review_count,
    count(*) filter (where review_answer_timestamp is not null)
      over (partition by source_run_id, order_id)::int as answered_review_count,
    row_number() over (
      partition by source_run_id, order_id
      order by
        (review_answer_timestamp is not null) desc,
        review_answer_timestamp desc nulls last,
        review_creation_date desc nulls last,
        review_id desc
    ) as review_rank
  from {{ ref('stg_order_reviews') }} r
)
select
  source_run_id,
  order_id,
  review_id,
  review_score,
  review_comment_title,
  review_comment_message,
  review_creation_date,
  review_answer_timestamp,
  review_count,
  answered_review_count
from ranked_reviews
where review_rank = 1

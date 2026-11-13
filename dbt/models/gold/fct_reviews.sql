select source_run_id, order_id, review_id, review_score, review_comment_title,
       review_comment_message, review_creation_date, review_answer_timestamp,
       review_count, answered_review_count
from {{ ref('order_reviews_canonical') }}

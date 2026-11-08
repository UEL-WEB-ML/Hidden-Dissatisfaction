select r.run_id as source_run_id, review_id::text, order_id::text, review_score::int, review_comment_title::text, review_comment_message::text, cast(nullif(trim(review_creation_date::text), '') as timestamp) as review_creation_date, cast(nullif(trim(review_answer_timestamp::text), '') as timestamp) as review_answer_timestamp
from {{ bronze_source('olist_order_reviews', 'r') }}

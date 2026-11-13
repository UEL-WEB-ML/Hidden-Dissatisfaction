with reviews as (
  select source_run_id, order_id, avg(review_score) as review_score,
         max(review_count)::int as review_count,
         max(answered_review_count)::int as answered_review_count
  from {{ ref('fct_reviews') }}
  group by source_run_id, order_id
)
select o.*, c.customer_unique_id, c.customer_city, c.customer_state,
       r.review_score, r.review_count, r.answered_review_count
from {{ ref('fct_orders') }} o
left join {{ ref('dim_customer') }} c using (source_run_id, customer_id)
left join reviews r using (source_run_id, order_id)

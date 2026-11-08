{{ config(materialized='table', schema='intermediate') }}

-- ADR-001: prefer answered reviews, then latest answer/creation, then review id.
with ranked as (
  select r.*, row_number() over (
    partition by source_run_id, order_id
    order by (review_answer_timestamp is not null) desc,
             review_answer_timestamp desc nulls last,
             review_creation_date desc nulls last, review_id desc
  ) as rn,
  count(*) over (partition by source_run_id, order_id)::int as review_count
  from {{ ref('stg_order_reviews') }} r
)
select source_run_id, order_id, review_id, review_score, review_creation_date,
       review_answer_timestamp, review_count
from ranked where rn = 1

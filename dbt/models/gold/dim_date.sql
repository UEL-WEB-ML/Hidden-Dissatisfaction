with bounds as (
  select source_run_id, min(order_purchase_timestamp)::date as min_date,
         max(order_purchase_timestamp)::date as max_date
  from {{ ref('stg_orders') }}
  group by source_run_id
), dates as (
  select source_run_id, generate_series(min_date, max_date, interval '1 day')::date as date_day
  from bounds
)
select source_run_id, date_day as date_key, extract(year from date_day)::int as year,
       extract(quarter from date_day)::int as quarter,
       extract(month from date_day)::int as month,
       extract(week from date_day)::int as week,
       extract(isodow from date_day)::int as day_of_week,
       extract(day from date_day)::int as day_of_month,
       extract(isodow from date_day)::int in (6, 7) as is_weekend
from dates

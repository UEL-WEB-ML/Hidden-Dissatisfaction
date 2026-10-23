{{ config(materialized='table', schema='intermediate') }}

select source_run_id, order_id,
       count(*)::int as payment_count,
       sum(payment_value) as payment_amount,
       max(payment_installments)::int as max_payment_installments
from {{ ref('stg_order_payments') }}
group by source_run_id, order_id

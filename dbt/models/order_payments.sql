select trim(order_id) order_id, nullif(trim(payment_sequential),'')::int payment_sequential, lower(trim(payment_type)) payment_type, nullif(trim(payment_installments),'')::int payment_installments, nullif(trim(payment_value),'')::numeric payment_value, run_id source_run_id, source_row_number
from {{ source('bronze','order_payments') }} where run_id='{{ var("source_run_id") }}'::uuid

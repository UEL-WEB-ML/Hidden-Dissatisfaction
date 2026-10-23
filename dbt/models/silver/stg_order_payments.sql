select p.run_id as source_run_id, order_id::text, payment_sequential::int, lower(nullif(trim(payment_type::text), '')) as payment_type, payment_installments::int, payment_value::numeric
from {{ bronze_source('olist_order_payments', 'p') }}

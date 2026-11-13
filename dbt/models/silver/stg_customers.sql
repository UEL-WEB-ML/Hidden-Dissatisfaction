select c.run_id as source_run_id, customer_id::text, customer_unique_id::text, customer_zip_code_prefix::text, lower(nullif(trim(customer_city::text), '')) as customer_city, upper(nullif(trim(customer_state::text), '')) as customer_state
from {{ bronze_source('olist_customers', 'c') }}

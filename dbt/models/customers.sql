select trim(customer_id) as customer_id, trim(customer_unique_id) as customer_unique_id,
       lpad(nullif(regexp_replace(customer_zip_code_prefix, '\\D', '', 'g'),''), 5, '0') as zip_code,
       lower(nullif(trim(customer_city),'')) as city, upper(nullif(trim(customer_state),'')) as state,
       run_id as source_run_id, source_row_number
from {{ source('bronze','customers') }} where run_id = '{{ var("source_run_id") }}'::uuid

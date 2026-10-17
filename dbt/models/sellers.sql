select trim(seller_id) seller_id, lpad(nullif(regexp_replace(seller_zip_code_prefix,'\\D','','g'),''), 5, '0') zip_code, lower(nullif(trim(seller_city),'')) city, upper(nullif(trim(seller_state),'')) state, run_id source_run_id, source_row_number
from {{ source('bronze','sellers') }} where run_id='{{ var("source_run_id") }}'::uuid

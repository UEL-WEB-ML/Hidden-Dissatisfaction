select s.run_id as source_run_id, seller_id::text, seller_zip_code_prefix::text, lower(nullif(trim(seller_city::text), '')) as seller_city, upper(nullif(trim(seller_state::text), '')) as seller_state
from {{ bronze_source('olist_sellers', 's') }}

select source_run_id, seller_id, seller_zip_code_prefix as zip_code_prefix, seller_city, seller_state
from {{ ref('stg_sellers') }}

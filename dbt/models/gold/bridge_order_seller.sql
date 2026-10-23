select distinct source_run_id, order_id, seller_id
from {{ ref('stg_order_items') }}

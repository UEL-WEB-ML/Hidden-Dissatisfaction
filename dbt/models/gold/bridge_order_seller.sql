select distinct source_run_id,order_id,seller_id from {{ ref('order_items') }} where seller_id is not null

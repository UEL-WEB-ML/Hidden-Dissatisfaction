select distinct oi.source_run_id, oi.order_id, p.category
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_products') }} p using (source_run_id, product_id)

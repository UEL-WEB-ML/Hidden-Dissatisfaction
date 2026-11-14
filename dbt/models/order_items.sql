select trim(order_id) order_id, nullif(trim(order_item_id),'')::int order_item_id, trim(product_id) product_id, trim(seller_id) seller_id,
 nullif(trim(shipping_limit_date),'')::timestamptz shipping_limit_at, nullif(trim(price),'')::numeric price, nullif(trim(freight_value),'')::numeric freight_value, run_id source_run_id, source_row_number
from {{ source('bronze','order_items') }} where run_id='{{ var("source_run_id") }}'::uuid

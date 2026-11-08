select i.run_id as source_run_id, order_id::text, order_item_id::int, product_id::text, seller_id::text, cast(nullif(trim(shipping_limit_date::text), '') as timestamp) as shipping_limit_date, price::numeric, freight_value::numeric
from {{ bronze_source('olist_order_items', 'i') }}

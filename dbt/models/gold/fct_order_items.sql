select source_run_id, order_id, order_item_id as item_id, product_id, seller_id,
       shipping_limit_date, price, freight_value,
       price + freight_value as item_plus_freight_amount
from {{ ref('stg_order_items') }}

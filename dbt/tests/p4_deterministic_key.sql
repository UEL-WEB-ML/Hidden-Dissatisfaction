select * from {{ ref('ml_modelling_items') }}
where product_item_id <> order_id || '-' || order_item_id

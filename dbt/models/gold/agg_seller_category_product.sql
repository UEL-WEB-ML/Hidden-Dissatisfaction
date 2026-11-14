select source_run_id,seller_id,product_id,count(*) item_count,sum(price) merchandise_amount from {{ ref('order_items') }} group by 1,2,3

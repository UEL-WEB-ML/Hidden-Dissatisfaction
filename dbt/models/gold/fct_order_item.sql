select i.*, o.customer_id from {{ ref('order_items') }} i left join {{ ref('orders') }} o using (order_id, source_run_id)

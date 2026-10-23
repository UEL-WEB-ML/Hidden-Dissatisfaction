select i.*, o.customer_id, o.order_status, o.order_purchase_timestamp,
       p.category, s.seller_state, c.customer_state
from {{ ref('fct_order_items') }} i
join {{ ref('fct_orders') }} o using (source_run_id, order_id)
left join {{ ref('dim_product') }} p using (source_run_id, product_id)
left join {{ ref('dim_seller') }} s using (source_run_id, seller_id)
left join {{ ref('dim_customer') }} c using (source_run_id, customer_id)

select source_run_id, product_item_id from {{ ref('int_p5_interactions') }}
where order_seller_category_complexity < 1 or delivery_buffer_to_duration_ratio < 0
   or seller_speed_x_freight_ratio < 0 or density_x_item_value_share < 0
   or purchase_delivery_zero_flag not in (0, 1)

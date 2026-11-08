select source_run_id, product_item_id from {{ ref('int_p5_temporal_features') }}
where purchase_month not between 1 and 12 or purchase_weekday not between 1 and 7
   or purchase_hour not between 0 and 23 or delivery_month not between 1 and 12
   or delivery_weekday not between 1 and 7 or delivery_dataset_age_days < 0
   or global_order_volume_7d < 0 or global_order_volume_30d < 0
   or seller_recent_order_volume_7d < 0 or seller_recent_order_volume_30d < 0
   or category_recent_order_volume_7d < 0 or category_recent_order_volume_30d < 0

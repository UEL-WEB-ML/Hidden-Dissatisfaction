select source_run_id, product_item_id from {{ ref('int_p5_data_quality') }}
where category_missing_flag not in (0, 1) or payment_missing_flag not in (0, 1)
   or customer_state_missing_flag not in (0, 1) or data_quality_carrier_delivery_missing_flag not in (0, 1)
   or item_data_quality_missing_count not between 0 and 4

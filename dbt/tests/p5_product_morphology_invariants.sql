select source_run_id, product_item_id from {{ ref('int_p5_product_morphology') }}
where product_volume_cm3 < 0 or product_density_g_cm3 < 0 or product_max_dimension_cm < 0
   or product_min_dimension_cm < 0 or product_dimension_ratio < 0 or freight_to_price_ratio < 0
   or freight_per_kg < 0 or photos_per_100_currency < 0 or product_name_length < 0
   or product_description_length < 0 or product_metadata_missing_count not between 0 and 7
   or product_max_dimension_cm < product_min_dimension_cm
   or product_dimensions_missing_flag not in (0, 1) or product_weight_missing_flag not in (0, 1)
   or product_photos_missing_flag not in (0, 1) or product_content_missing_flag not in (0, 1)
   or product_price_zero_flag not in (0, 1) or product_weight_zero_flag not in (0, 1)

select source_run_id, product_item_id
from {{ ref('int_p5_target_history') }}
where target_history_prior_strength <= 0
   or global_prior_negative_count > global_prior_order_count
   or seller_negative_history_negative_count > seller_negative_history_count
   or category_negative_history_negative_count > category_negative_history_count
   or global_prior_order_count_30d > global_prior_order_count_90d
   or global_prior_order_count_90d > global_prior_order_count
   or seller_negative_history_count_30d > seller_negative_history_count_90d
   or seller_negative_history_count_90d > seller_negative_history_count
   or category_negative_history_count_30d > category_negative_history_count_90d
   or category_negative_history_count_90d > category_negative_history_count
   or global_prior_negative_rate not between 0 and 1
   or global_prior_negative_rate_30d not between 0 and 1
   or global_prior_negative_rate_90d not between 0 and 1
   or seller_smoothed_negative_rate not between 0 and 1
   or seller_smoothed_negative_rate_30d not between 0 and 1
   or seller_smoothed_negative_rate_90d not between 0 and 1
   or category_smoothed_negative_rate not between 0 and 1
   or category_smoothed_negative_rate_30d not between 0 and 1
   or category_smoothed_negative_rate_90d not between 0 and 1
   or seller_category_smoothed_negative_rate not between 0 and 1
   or seller_negative_history_cold_start_flag <> (seller_negative_history_count = 0)::int
   or seller_negative_history_low_support_flag
      <> (seller_negative_history_count between 1 and 4)::int
   or category_negative_history_cold_start_flag <> (category_negative_history_count = 0)::int
   or category_negative_history_low_support_flag
      <> (category_negative_history_count between 1 and 4)::int
   or seller_category_negative_history_cold_start_flag
      <> (seller_category_negative_history_count = 0)::int
   or seller_category_negative_history_low_support_flag
      <> (seller_category_negative_history_count between 1 and 4)::int
   or (seller_negative_history_count = 0
       and abs(seller_smoothed_negative_rate - global_prior_negative_rate) > 0.000000001)
   or (category_negative_history_count = 0
       and abs(category_smoothed_negative_rate - global_prior_negative_rate) > 0.000000001)

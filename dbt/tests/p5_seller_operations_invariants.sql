select source_run_id, product_item_id
from {{ ref('int_p5_seller_operations') }}
where seller_operational_prior_order_count_30d > seller_operational_prior_order_count_90d
   or seller_operational_prior_order_count_90d > seller_operational_prior_order_count
   or seller_operational_prior_item_count < seller_operational_prior_order_count
   or seller_operational_cold_start_flag
      <> (seller_operational_prior_order_count = 0)::int
   or seller_prior_late_shipping_rate not between 0 and 1
   or seller_prior_late_delivery_rate not between 0 and 1
   or seller_prior_late_delivery_rate_30d not between 0 and 1
   or seller_prior_late_delivery_rate_90d not between 0 and 1
   or (seller_operational_prior_order_count = 0 and (
       seller_mean_approval_to_carrier_days is not null
       or seller_mean_carrier_to_delivery_days is not null
       or seller_mean_purchase_to_delivery_days is not null
       or seller_days_since_previous_delivery is not null
   ))

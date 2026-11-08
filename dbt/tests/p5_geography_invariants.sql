select source_run_id,product_item_id
from {{ ref('int_p5_geography') }}
where seller_customer_distance_km < 0 or seller_customer_distance_km > 5000
   or same_state_flag not in (0,1) or cross_state_flag not in (0,1)
   or same_city_flag not in (0,1) or seller_centroid_missing_flag not in (0,1)
   or customer_centroid_missing_flag not in (0,1) or route_distance_missing_flag not in (0,1)
   or (same_state_flag=1 and cross_state_flag=1)
   or (route_distance_missing_flag=1 and seller_customer_distance_km is not null)
   or (route_distance_missing_flag=0 and seller_customer_distance_km is null)

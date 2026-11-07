{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

with joined as (
 select c.source_run_id,c.product_item_id,c.customer_state,c.customer_city,
        s.seller_state,s.seller_city,
        cz.lat customer_lat,cz.lng customer_lng,sz.lat seller_lat,sz.lng seller_lng
 from {{ ref('int_p4_cohort') }} c
 left join {{ ref('dim_seller') }} s using(source_run_id,seller_id)
 left join {{ ref('dim_zip_centroid') }} cz
   on cz.source_run_id=c.source_run_id and cz.zip_code_prefix=c.zip_code_prefix
 left join {{ ref('dim_zip_centroid') }} sz
   on sz.source_run_id=c.source_run_id and sz.zip_code_prefix=s.zip_code_prefix
), components as (
 select *,
  power(sin(radians(customer_lat-seller_lat)/2),2)
  +cos(radians(seller_lat))*cos(radians(customer_lat))
   *power(sin(radians(customer_lng-seller_lng)/2),2) haversine_component
 from joined
)
select source_run_id,product_item_id,
 case when customer_lat is not null and customer_lng is not null
        and seller_lat is not null and seller_lng is not null
      then 2*6371.0088*asin(sqrt(least(1.0,greatest(0.0,haversine_component)))) end
   seller_customer_distance_km,
 (seller_state is not null and customer_state is not null and seller_state=customer_state)::int same_state_flag,
 (seller_state is not null and customer_state is not null and seller_state<>customer_state)::int cross_state_flag,
 (seller_city is not null and customer_city is not null and seller_city=customer_city)::int same_city_flag,
 (seller_lat is null or seller_lng is null)::int seller_centroid_missing_flag,
 (customer_lat is null or customer_lng is null)::int customer_centroid_missing_flag,
 (seller_lat is null or seller_lng is null or customer_lat is null or customer_lng is null)::int route_distance_missing_flag,
 coalesce(seller_state,'(missing)')||'->'||coalesce(customer_state,'(missing)') route_pair,
 'p5-geography-v1' geography_version
from components

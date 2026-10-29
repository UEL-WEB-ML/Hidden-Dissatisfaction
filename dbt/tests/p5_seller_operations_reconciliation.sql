with sampled as (
 select * from {{ ref('int_p4_cohort') }}
 where mod(hashtextextended(product_item_id,0),211)=0
), events as (
 select i.source_run_id,i.order_id,i.seller_id,min(o.order_delivered_customer_date) delivered_at
 from {{ ref('stg_order_items') }} i join {{ ref('stg_orders') }} o using(source_run_id,order_id)
 where o.order_status='delivered' and o.order_delivered_customer_date is not null
 group by i.source_run_id,i.order_id,i.seller_id
), expected as (
 select c.source_run_id,c.product_item_id,count(e.order_id)::int prior_orders
 from sampled c left join events e on e.source_run_id=c.source_run_id and e.seller_id=c.seller_id
  and e.delivered_at<c.prediction_at and e.order_id<>c.order_id
 group by c.source_run_id,c.product_item_id
)
select s.source_run_id,s.product_item_id
from {{ ref('int_p5_seller_operations') }} s join expected e using(source_run_id,product_item_id)
where s.seller_operational_prior_order_count<>e.prior_orders

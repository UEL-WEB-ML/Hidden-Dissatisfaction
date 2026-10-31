{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

with operational_events as (
 select i.source_run_id, i.order_id, i.seller_id,
        min(o.order_purchase_timestamp) purchase_at,
        min(o.order_delivered_customer_date) delivered_at,
        count(*)::int item_count,
        extract(epoch from (min(o.order_delivered_carrier_date)-min(o.order_approved_at)))/86400.0 approval_carrier_days,
        extract(epoch from (min(o.order_delivered_customer_date)-min(o.order_delivered_carrier_date)))/86400.0 carrier_delivery_days,
        extract(epoch from (min(o.order_delivered_customer_date)-min(o.order_purchase_timestamp)))/86400.0 purchase_delivery_days,
        bool_or(o.order_delivered_carrier_date > i.shipping_limit_date)::int late_shipping,
        (min(o.order_delivered_customer_date) > min(o.order_estimated_delivery_date))::int late_delivery,
        sum(i.freight_value)/nullif(sum(i.price),0) freight_value_ratio
 from {{ ref('stg_order_items') }} i join {{ ref('stg_orders') }} o using(source_run_id,order_id)
 where o.order_status='delivered' and o.order_delivered_customer_date is not null
 group by i.source_run_id,i.order_id,i.seller_id
), queries as (
 select source_run_id,product_item_id,seller_id,prediction_at timeline_at,0::int kind,
  0::int n,0::int items, null::timestamp purchase_at,null::timestamp delivered_at,
  0::int approval_n,0::numeric approval_sum,0::int carrier_n,0::numeric carrier_sum,
  0::int delivery_n,0::numeric delivery_sum,0::numeric delivery_sumsq,
  0::int freight_n,0::numeric freight_sum,0::numeric freight_sumsq,
  0::int late_shipping_sum,0::int late_delivery_sum,
  0::int n30,0::numeric delivery_sum30,0::int delivery_n30,0::int late_delivery30,
  0::int n90,0::numeric delivery_sum90,0::int delivery_n90,0::int late_delivery90
 from {{ ref('int_p4_cohort') }}
), additions as (
 select source_run_id,null::text product_item_id,seller_id,delivered_at timeline_at,1::int kind,
  1::int n,item_count items,purchase_at,delivered_at,
  (approval_carrier_days is not null)::int approval_n,coalesce(approval_carrier_days,0) approval_sum,
  (carrier_delivery_days is not null)::int carrier_n,coalesce(carrier_delivery_days,0) carrier_sum,
  (purchase_delivery_days is not null)::int delivery_n,coalesce(purchase_delivery_days,0) delivery_sum,
  coalesce(purchase_delivery_days*purchase_delivery_days,0) delivery_sumsq,
  (freight_value_ratio is not null)::int freight_n,coalesce(freight_value_ratio,0) freight_sum,
  coalesce(freight_value_ratio*freight_value_ratio,0) freight_sumsq,
  late_shipping late_shipping_sum,late_delivery late_delivery_sum,
  1::int n30,coalesce(purchase_delivery_days,0) delivery_sum30,
  (purchase_delivery_days is not null)::int delivery_n30,late_delivery late_delivery30,
  1::int n90,coalesce(purchase_delivery_days,0) delivery_sum90,
  (purchase_delivery_days is not null)::int delivery_n90,late_delivery late_delivery90
 from operational_events
), expirations as (
 select source_run_id,null::text product_item_id,seller_id,delivered_at+window_size timeline_at,1::int kind,
  0::int n,0::int items,null::timestamp purchase_at,null::timestamp delivered_at,
  0::int approval_n,0::numeric approval_sum,0::int carrier_n,0::numeric carrier_sum,
  0::int delivery_n,0::numeric delivery_sum,0::numeric delivery_sumsq,
  0::int freight_n,0::numeric freight_sum,0::numeric freight_sumsq,
  0::int late_shipping_sum,0::int late_delivery_sum,
  case when window_size=interval '30 days' then -1 else 0 end n30,
  case when window_size=interval '30 days' then -coalesce(purchase_delivery_days,0) else 0 end delivery_sum30,
  case when window_size=interval '30 days' then -(purchase_delivery_days is not null)::int else 0 end delivery_n30,
  case when window_size=interval '30 days' then -late_delivery else 0 end late_delivery30,
  case when window_size=interval '90 days' then -1 else 0 end n90,
  case when window_size=interval '90 days' then -coalesce(purchase_delivery_days,0) else 0 end delivery_sum90,
  case when window_size=interval '90 days' then -(purchase_delivery_days is not null)::int else 0 end delivery_n90,
  case when window_size=interval '90 days' then -late_delivery else 0 end late_delivery90
 from operational_events cross join(values(interval '30 days'),(interval '90 days')) w(window_size)
), timeline as (select * from queries union all select * from additions union all select * from expirations),
cumulative as (
 select *,sum(n) over h prior_orders,sum(items) over h prior_items,
  min(purchase_at) over h first_purchase_at,min(delivered_at) over h first_delivered_at,max(delivered_at) over h previous_delivered_at,
  sum(approval_n) over h approval_count,sum(approval_sum) over h approval_total,
  sum(carrier_n) over h carrier_count,sum(carrier_sum) over h carrier_total,
  sum(delivery_n) over h delivery_count,sum(delivery_sum) over h delivery_total,sum(delivery_sumsq) over h delivery_total_sq,
  sum(freight_n) over h freight_count,sum(freight_sum) over h freight_total,sum(freight_sumsq) over h freight_total_sq,
  sum(late_shipping_sum) over h late_shipping_total,sum(late_delivery_sum) over h late_delivery_total,
  sum(n30) over h prior_orders30,sum(delivery_sum30) over h delivery_total30,sum(delivery_n30) over h delivery_count30,
  sum(late_delivery30) over h late_delivery_total30,sum(n90) over h prior_orders90,
  sum(delivery_sum90) over h delivery_total90,sum(delivery_n90) over h delivery_count90,sum(late_delivery90) over h late_delivery_total90
 from timeline window h as(partition by source_run_id,seller_id order by timeline_at,kind rows between unbounded preceding and current row)
), f as (select * from cumulative where product_item_id is not null)
select source_run_id,product_item_id,prior_orders::int seller_operational_prior_order_count,
 prior_items::int seller_operational_prior_item_count,prior_orders30::int seller_operational_prior_order_count_30d,
 prior_orders90::int seller_operational_prior_order_count_90d,prior_orders30/30.0 seller_operational_volume_velocity_30d,
 extract(epoch from(timeline_at-first_purchase_at))/86400.0 seller_days_since_first_observed_order,
 extract(epoch from(timeline_at-first_delivered_at))/86400.0 seller_days_since_first_delivered_order,
 extract(epoch from(timeline_at-previous_delivered_at))/86400.0 seller_days_since_previous_delivery,
 (prior_orders=0)::int seller_operational_cold_start_flag,
 approval_total/nullif(approval_count,0) seller_mean_approval_to_carrier_days,
 carrier_total/nullif(carrier_count,0) seller_mean_carrier_to_delivery_days,
 delivery_total/nullif(delivery_count,0) seller_mean_purchase_to_delivery_days,
 sqrt(greatest(0,delivery_total_sq/nullif(delivery_count,0)-power(delivery_total/nullif(delivery_count,0),2))) seller_std_purchase_to_delivery_days,
 sqrt(greatest(0,delivery_total_sq/nullif(delivery_count,0)-power(delivery_total/nullif(delivery_count,0),2)))/nullif(delivery_total/nullif(delivery_count,0),0) seller_delivery_cv,
 freight_total/nullif(freight_count,0) seller_mean_freight_value_ratio,
 sqrt(greatest(0,freight_total_sq/nullif(freight_count,0)-power(freight_total/nullif(freight_count,0),2))) seller_std_freight_value_ratio,
 late_shipping_total::numeric/nullif(prior_orders,0) seller_prior_late_shipping_rate,
 late_delivery_total::numeric/nullif(prior_orders,0) seller_prior_late_delivery_rate,
 delivery_total30/nullif(delivery_count30,0) seller_mean_purchase_to_delivery_days_30d,
 delivery_total90/nullif(delivery_count90,0) seller_mean_purchase_to_delivery_days_90d,
 delivery_total30/nullif(delivery_count30,0)-delivery_total/nullif(delivery_count,0) seller_recent_vs_long_delivery_delta,
 late_delivery_total30::numeric/nullif(prior_orders30,0) seller_prior_late_delivery_rate_30d,
 late_delivery_total90::numeric/nullif(prior_orders90,0) seller_prior_late_delivery_rate_90d,
 late_delivery_total30::numeric/nullif(prior_orders30,0)-late_delivery_total90::numeric/nullif(prior_orders90,0) seller_late_delivery_rate_30d_vs_90d,
 'p5-seller-operations-v1' seller_operations_version
from f

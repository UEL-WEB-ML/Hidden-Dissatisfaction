with items as (
  select source_run_id, order_id, count(*)::int as item_count, sum(price) as item_amount,
         sum(freight_value) as freight_amount,
         sum(price + freight_value) as item_plus_freight_amount
  from {{ ref('stg_order_items') }} group by source_run_id, order_id
), payments as (
  select source_run_id, order_id, count(*)::int as payment_count, sum(payment_value) as payment_amount
  from {{ ref('stg_order_payments') }} group by source_run_id, order_id
)
select o.source_run_id, o.order_id, o.customer_id, o.order_status, o.order_purchase_timestamp,
       o.order_approved_at, o.order_delivered_carrier_date,
       o.order_delivered_customer_date, o.order_estimated_delivery_date,
       coalesce(i.item_count, 0) as item_count, coalesce(i.item_amount, 0) as item_amount,
       coalesce(i.freight_amount, 0) as freight_amount,
       coalesce(i.item_plus_freight_amount, 0) as item_plus_freight_amount,
       coalesce(p.payment_count, 0) as payment_count,
       coalesce(p.payment_amount, 0) as payment_amount
from {{ ref('stg_orders') }} o
left join items i using (source_run_id, order_id)
left join payments p using (source_run_id, order_id)

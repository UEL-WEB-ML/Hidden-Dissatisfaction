select trim(order_id) order_id, trim(customer_id) customer_id, lower(trim(order_status)) order_status,
       nullif(trim(order_purchase_timestamp),'')::timestamptz purchase_at,
       nullif(trim(order_approved_at),'')::timestamptz approved_at,
       nullif(trim(order_delivered_carrier_date),'')::timestamptz delivered_carrier_at,
       nullif(trim(order_delivered_customer_date),'')::timestamptz delivered_customer_at,
       nullif(trim(order_estimated_delivery_date),'')::timestamptz estimated_delivery_at,
       run_id source_run_id, source_row_number
from {{ source('bronze','orders') }} where run_id = '{{ var("source_run_id") }}'::uuid

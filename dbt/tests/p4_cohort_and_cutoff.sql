select * from {{ ref('ml_modelling_items') }}
where prediction_at is null or order_estimated_delivery_date is null
   or prediction_at > order_estimated_delivery_date
   or order_weight is null or order_weight <= 0

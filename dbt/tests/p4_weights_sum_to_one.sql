select source_run_id, order_id, sum(order_weight) as weight_sum
from {{ ref('ml_modelling_items') }}
group by source_run_id, order_id
having abs(sum(order_weight) - 1.0) > 0.000001

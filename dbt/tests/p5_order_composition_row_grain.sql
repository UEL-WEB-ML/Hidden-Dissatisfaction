select coalesce(c.source_run_id, o.source_run_id) as source_run_id,
       coalesce(c.product_item_id, o.product_item_id) as product_item_id
from {{ ref('int_p4_cohort') }} c
full outer join {{ ref('int_p5_order_composition') }} o
  using (source_run_id, product_item_id)
where c.product_item_id is null or o.product_item_id is null

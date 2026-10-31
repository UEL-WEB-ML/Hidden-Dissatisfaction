select coalesce(c.source_run_id, m.source_run_id) as source_run_id,
       coalesce(c.product_item_id, m.product_item_id) as product_item_id
from {{ ref('int_p4_cohort') }} c full outer join {{ ref('int_p5_product_morphology') }} m
  using (source_run_id, product_item_id)
where c.product_item_id is null or m.product_item_id is null

select coalesce(c.source_run_id, s.source_run_id) source_run_id,
       coalesce(c.product_item_id, s.product_item_id) product_item_id
from {{ ref('int_p4_cohort') }} c
full outer join {{ ref('int_p5_seller_operations') }} s using(source_run_id,product_item_id)
where c.product_item_id is null or s.product_item_id is null

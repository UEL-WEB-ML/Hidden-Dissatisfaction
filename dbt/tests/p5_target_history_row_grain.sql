with cohort as (
    select source_run_id, product_item_id
    from {{ ref('int_p4_cohort') }}
),
history as (
    select source_run_id, product_item_id
    from {{ ref('int_p5_target_history') }}
)
select coalesce(c.source_run_id, h.source_run_id) as source_run_id,
       coalesce(c.product_item_id, h.product_item_id) as product_item_id
from cohort c
full outer join history h using (source_run_id, product_item_id)
where c.product_item_id is null or h.product_item_id is null

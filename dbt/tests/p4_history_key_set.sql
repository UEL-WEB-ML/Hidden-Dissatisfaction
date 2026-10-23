{{ config(tags=['p4_fast', 'invariant']) }}
with cohort as (
    select distinct source_run_id, product_item_id from {{ ref('int_p4_cohort') }}
), history as (
    select distinct source_run_id, product_item_id from {{ ref('ml_modelling_items') }}
)
select coalesce(c.source_run_id, h.source_run_id) source_run_id,
       coalesce(c.product_item_id, h.product_item_id) product_item_id
from cohort c full outer join history h using (source_run_id, product_item_id)
where c.product_item_id is null or h.product_item_id is null

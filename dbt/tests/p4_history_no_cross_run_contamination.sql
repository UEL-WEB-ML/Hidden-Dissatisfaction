{{ config(tags=['p4_fast', 'invariant']) }}
select source_run_id, product_item_id
from {{ ref('int_p4_history') }}
group by source_run_id, product_item_id
having count(*) <> 1
union all
select source_run_id, product_item_id
from {{ ref('ml_modelling_items') }}
group by source_run_id, product_item_id
having count(*) <> 1

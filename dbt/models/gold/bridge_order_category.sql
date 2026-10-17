select distinct i.source_run_id,i.order_id,p.category_name_code category_code from {{ ref('order_items') }} i join {{ ref('product_enriched') }} p using(product_id,source_run_id)

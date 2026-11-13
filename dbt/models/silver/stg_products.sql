select p.run_id as source_run_id, p.product_id::text, lower(nullif(trim(p.product_category_name::text), '')) as product_category_name, lower(trim(coalesce(t.product_category_name_english, p.product_category_name, '(missing)')::text)) as category, p.product_name_lenght::int, p.product_description_lenght::int, p.product_photos_qty::int, p.product_weight_g::numeric, p.product_length_cm::numeric, p.product_height_cm::numeric, p.product_width_cm::numeric
from {{ bronze_source('olist_products', 'p') }}
left join {{ bronze_source('product_category_name_translation', 't') }}
  on p.run_id = t.run_id
 and p.product_category_name = t.product_category_name

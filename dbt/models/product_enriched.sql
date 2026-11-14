select p.*, coalesce(c.category_name,'__unknown__') category_name_code, c.category_name_english,
 coalesce(c.category_missing,true) category_missing, coalesce(c.has_translation,false) translation_missing
from {{ ref('products') }} p left join {{ ref('category_lookup') }} c
 on coalesce(lower(p.category_name),'__unknown__')=c.category_name and p.source_run_id=c.source_run_id

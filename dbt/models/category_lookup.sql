with categories as (
 select coalesce(category_name,'__unknown__') category_name, max(category_name_english) category_name_english,
 bool_or(not translation_missing) has_translation, bool_or(category_missing) category_missing, source_run_id
 from {{ ref('category_translations') }} group by 1, source_run_id
), unknown as (
 select '__unknown__' category_name, null::text category_name_english, false has_translation, true category_missing, '{{ var("source_run_id") }}'::uuid source_run_id
 where not exists (select 1 from categories where category_name='__unknown__')
)
select * from categories union all select * from unknown

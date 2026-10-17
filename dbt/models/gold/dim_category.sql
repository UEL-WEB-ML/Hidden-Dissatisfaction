select category_name category_code, category_name_english, has_translation, category_missing, source_run_id from {{ ref('category_lookup') }}

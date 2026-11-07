{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

-- Product metadata is available before order delivery.  Nulls remain null in
-- the derived measurements; explicit flags/counts distinguish absent metadata
-- from a genuine zero without inventing a physical value.
with product_data as (
    select c.source_run_id, c.product_item_id, c.product_id, c.price, c.freight_value,
           c.product_photos_qty, c.product_weight_g, c.product_length_cm,
           c.product_height_cm, c.product_width_cm, p.product_name_lenght,
           p.product_description_lenght
    from {{ ref('int_p4_cohort') }} c
    left join {{ ref('stg_products') }} p using (source_run_id, product_id)
), dimensions as (
    select *,
           case when product_length_cm > 0 and product_height_cm > 0 and product_width_cm > 0
                then greatest(product_length_cm, product_height_cm, product_width_cm) end as product_max_dimension_cm,
           case when product_length_cm > 0 and product_height_cm > 0 and product_width_cm > 0
                then least(product_length_cm, product_height_cm, product_width_cm) end as product_min_dimension_cm,
           case when product_length_cm > 0 and product_height_cm > 0 and product_width_cm > 0
                then product_length_cm * product_height_cm * product_width_cm end as product_volume_cm3
    from product_data
)
select source_run_id, product_item_id, product_volume_cm3,
       product_weight_g / nullif(product_volume_cm3, 0) as product_density_g_cm3,
       product_max_dimension_cm, product_min_dimension_cm,
       product_max_dimension_cm / nullif(product_min_dimension_cm, 0) as product_dimension_ratio,
       freight_value / nullif(price, 0) as freight_to_price_ratio,
       freight_value / nullif(product_weight_g / 1000.0, 0) as freight_per_kg,
       product_photos_qty / nullif(price / 100.0, 0) as photos_per_100_currency,
       product_name_lenght as product_name_length,
       product_description_lenght as product_description_length,
       ((product_photos_qty is null)::int + (product_weight_g is null)::int
        + (product_length_cm is null)::int + (product_height_cm is null)::int
        + (product_width_cm is null)::int + (product_name_lenght is null)::int
        + (product_description_lenght is null)::int)::int as product_metadata_missing_count,
       (product_length_cm is null or product_height_cm is null or product_width_cm is null)::int as product_dimensions_missing_flag,
       (product_weight_g is null)::int as product_weight_missing_flag,
       (product_photos_qty is null)::int as product_photos_missing_flag,
       (product_name_lenght is null or product_description_lenght is null)::int as product_content_missing_flag,
       coalesce((price = 0)::int, 0) as product_price_zero_flag,
       coalesce((product_weight_g = 0)::int, 0) as product_weight_zero_flag,
       'p5-product-morphology-v1' as product_morphology_version
from dimensions

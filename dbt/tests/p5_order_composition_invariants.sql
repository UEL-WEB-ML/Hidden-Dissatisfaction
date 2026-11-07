select source_run_id, product_item_id
from {{ ref('int_p5_order_composition') }}
where order_seller_count < 1
   or order_category_count < 1
   or order_product_count < 1
   or order_unique_product_count < 1
   or order_item_count < 1
   or order_seller_count > order_item_count
   or order_category_count > order_item_count
   or order_product_count > order_item_count
   or order_unique_product_count > order_item_count
   or order_unique_product_count > order_product_count
   or order_freight_share not between 0 and 1
   or order_max_item_value_share not between 0 and 1
   or order_min_item_value_share not between 0 and 1
   or order_min_item_value_share > order_max_item_value_share
   or order_category_hhi not between 0 and 1
   or order_seller_hhi not between 0 and 1
   or multi_item_flag not in (0, 1)
   or multi_seller_flag not in (0, 1)
   or multi_category_flag not in (0, 1)

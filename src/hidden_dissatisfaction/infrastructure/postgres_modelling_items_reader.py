"""Postgres adapter for the allowlisted Gold modelling-items relation."""

from collections.abc import Iterable, Mapping
from typing import Any

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.application.modelling_export import GoldModellingItemsReader


class PostgresGoldModellingItemsReader(GoldModellingItemsReader):
    """Read one deterministic, source-run-scoped snapshot from Gold."""

    def __init__(self, dsn: str, source_run_id: str) -> None:
        self.dsn = dsn
        self.source_run_id = source_run_id

    def read_modelling_items(self) -> Iterable[Mapping[str, Any]]:
        query = """
            SELECT product_item_id, source_run_id, order_id, order_item_id,
                   product_id, seller_id, product_category, customer_id,
                   prediction_at, delivered_customer_date, order_purchase_timestamp,
                   order_delivered_carrier_date, order_estimated_delivery_date,
                   price, freight_value, item_plus_freight_amount, payment_count,
                   payment_amount, max_payment_installments, order_weight,
                   estimated_delivery_buffer_days, purchase_to_delivery_days,
                   carrier_to_delivery_days, product_photos_qty, product_weight_g,
                   product_length_cm, product_height_cm, product_width_cm,
                   order_item_count, order_item_value_total, item_value_share,
                   canonical_review_score, negative, review_created_at, review_id,
                   review_multiplicity, review_resolution, review_policy_version,
                   cohort_version, history_version, feature_schema_version,
                   customer_city, customer_state, zip_code_prefix, on_time_flag,
                   geography_missing_flag, carrier_delivery_missing_flag,
                   seller_prior_review_count, seller_prior_review_score_avg,
                   seller_history_low_support_flag, category_prior_review_count,
                   category_prior_review_score_avg, category_history_low_support_flag,
                   target_history_version, global_prior_order_count,
                   global_prior_negative_count, global_prior_negative_rate,
                   global_prior_order_count_30d, global_prior_negative_rate_30d,
                   global_prior_order_count_90d, global_prior_negative_rate_90d,
                   seller_negative_history_count,
                   seller_negative_history_negative_count,
                   seller_negative_history_support_log1p,
                   seller_negative_history_cold_start_flag,
                   seller_negative_history_low_support_flag,
                   seller_smoothed_negative_rate,
                   seller_negative_history_score_mean,
                   seller_negative_history_count_30d,
                   seller_smoothed_negative_rate_30d,
                   seller_negative_history_score_mean_30d,
                   seller_negative_history_count_90d,
                   seller_smoothed_negative_rate_90d,
                   seller_negative_history_score_mean_90d,
                   category_negative_history_count,
                   category_negative_history_negative_count,
                   category_negative_history_support_log1p,
                   category_negative_history_cold_start_flag,
                   category_negative_history_low_support_flag,
                   category_smoothed_negative_rate,
                   category_negative_history_count_30d,
                   category_smoothed_negative_rate_30d,
                   category_negative_history_count_90d,
                   category_smoothed_negative_rate_90d,
                   seller_category_negative_history_count,
                   seller_category_negative_history_support_log1p,
                   seller_category_negative_history_cold_start_flag,
                   seller_category_negative_history_low_support_flag,
                   seller_category_smoothed_negative_rate,
                   target_history_prior_strength,
                   seller_operations_version,
                   seller_operational_prior_order_count,
                   seller_operational_prior_item_count,
                   seller_operational_prior_order_count_30d,
                   seller_operational_prior_order_count_90d,
                   seller_operational_volume_velocity_30d,
                   seller_days_since_first_observed_order,
                   seller_days_since_first_delivered_order,
                   seller_days_since_previous_delivery,
                   seller_operational_cold_start_flag,
                   seller_mean_approval_to_carrier_days,
                   seller_mean_carrier_to_delivery_days,
                   seller_mean_purchase_to_delivery_days,
                   seller_std_purchase_to_delivery_days,
                   seller_delivery_cv, seller_mean_freight_value_ratio,
                   seller_std_freight_value_ratio,
                   seller_prior_late_shipping_rate,
                   seller_prior_late_delivery_rate,
                   seller_mean_purchase_to_delivery_days_30d,
                   seller_mean_purchase_to_delivery_days_90d,
                   seller_recent_vs_long_delivery_delta,
                   seller_prior_late_delivery_rate_30d,
                   seller_prior_late_delivery_rate_90d,
                   seller_late_delivery_rate_30d_vs_90d,
                   geography_version, seller_customer_distance_km,
                   same_state_flag, cross_state_flag, same_city_flag,
                   seller_centroid_missing_flag, customer_centroid_missing_flag,
                   route_distance_missing_flag, route_pair,
                   order_composition_version, order_seller_count,
                   order_category_count, order_product_count,
                   order_unique_product_count, order_freight_total,
                   order_freight_share, order_max_item_value_share,
                   order_min_item_value_share, order_price_mean, order_price_std,
                   order_price_max, order_price_min, order_freight_mean,
                   order_freight_std, order_freight_max, order_category_hhi,
                   order_seller_hhi, multi_item_flag, multi_seller_flag,
                   multi_category_flag,
                   payment_behavior_version, payment_type_count,
                   payment_installments_mean, installment_amount,
                   payment_to_order_value_ratio, credit_card_payment_share,
                   voucher_payment_share, payment_type_hhi, split_payment_flag,
                   mixed_payment_type_flag, credit_card_payment_flag,
                   boleto_payment_flag, voucher_payment_flag, debit_card_payment_flag,
                   payment_order_value_zero_flag, primary_payment_type,
                   product_morphology_version, product_volume_cm3,
                   product_density_g_cm3, product_max_dimension_cm,
                   product_min_dimension_cm, product_dimension_ratio,
                   freight_to_price_ratio, freight_per_kg, photos_per_100_currency,
                   product_name_length, product_description_length,
                   product_metadata_missing_count, product_dimensions_missing_flag,
                   product_weight_missing_flag, product_photos_missing_flag,
                   product_content_missing_flag, product_price_zero_flag,
                   product_weight_zero_flag,
                   temporal_features_version, purchase_month, purchase_weekday,
                   purchase_hour, delivery_month, delivery_weekday,
                   delivery_dataset_age_days, global_order_volume_7d,
                   global_order_volume_30d, seller_recent_order_volume_7d,
                   seller_recent_order_volume_30d, category_recent_order_volume_7d,
                   category_recent_order_volume_30d, category_recent_volume_delta,
                   data_quality_version, category_missing_flag, payment_missing_flag,
                   customer_state_missing_flag, data_quality_carrier_delivery_missing_flag,
                   item_data_quality_missing_count,
                   interactions_version, order_seller_category_complexity,
                   delivery_buffer_to_duration_ratio, seller_speed_x_freight_ratio,
                   density_x_item_value_share, purchase_delivery_zero_flag,
                   feature_set_version, observation_window_version
            FROM gold.ml_modelling_items
            WHERE source_run_id = %s
            ORDER BY order_id, order_item_id
        """
        with psycopg.connect(self.dsn, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (self.source_run_id,))
                rows = cursor.fetchall()
        if any(str(row.get("source_run_id")) != self.source_run_id for row in rows):
            raise ValueError("Gold rows contain a source_run_id different from the requested run")
        return rows

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
                   canonical_review_score, negative, review_created_at, review_id,
                   review_multiplicity, review_resolution, review_policy_version,
                   cohort_version, history_version, feature_schema_version,
                   customer_city, customer_state, zip_code_prefix, on_time_flag,
                   geography_missing_flag, carrier_delivery_missing_flag,
                   seller_prior_review_count, seller_prior_review_score_avg,
                   seller_history_low_support_flag, category_prior_review_count,
                   category_prior_review_score_avg, category_history_low_support_flag,
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

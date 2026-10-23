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
            SELECT *
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

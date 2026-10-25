"""PostgreSQL order-grain projection for the Risk Queue."""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.application.queue import QueueOrder, QueuePage
from hidden_dissatisfaction.domain.queue import PRODUCT_ITEM_ID, QueueFilters


class PostgresRiskOrderQuery:
    """Execute the Queue read model without exposing persistence rows to HTTP."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def list_orders(self, filters: QueueFilters) -> QueuePage:
        where, params, matched_item_id = self._where_clause(filters)
        order_by = {
            "priority": "r.risk_score DESC, cycle.sla_due_at ASC NULLS LAST, c.original_queued_at ASC, c.order_id ASC",
            "sla": "cycle.sla_due_at ASC NULLS LAST, r.risk_score DESC, c.order_id ASC",
            "aging": "c.original_queued_at ASC, r.risk_score DESC, c.order_id ASC",
        }[filters.sort]
        projection = """
            FROM app.review_cases c
            JOIN ml.v_risk_orders_for_web r
              ON r.prediction_id = c.prediction_id AND r.order_id = c.order_id
            LEFT JOIN app.assignments a ON a.case_id = c.case_id AND a.released_at IS NULL
            LEFT JOIN app.users u ON u.user_id = a.assignee_id
            LEFT JOIN LATERAL (
                SELECT cycle_id, started_at, sla_due_at FROM app.review_cycles
                WHERE case_id = c.case_id AND ended_at IS NULL
                ORDER BY cycle_no DESC LIMIT 1
            ) cycle ON TRUE
        """
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            total = connection.execute(
                f"SELECT count(*) AS total {projection} {where}", params
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT c.order_id, r.risk_score, r.risk_level, c.status, a.assignee_id,
                       u.username AS assignee_name, c.original_queued_at, cycle.sla_due_at, c.row_version
                {projection} {where}
                ORDER BY {order_by}
                LIMIT %(limit)s OFFSET %(offset)s
                """,
                params | {"limit": filters.limit, "offset": filters.offset},
            ).fetchall()
        return QueuePage(
            items=tuple(self._to_order(row, matched_item_id) for row in rows),
            total=int(self._require_row(total)["total"]),
        )

    def filter_options(self) -> dict[str, tuple[str, ...]]:
        """Return stable seller/category filter values from the active risk snapshot."""
        sql = """
            SELECT DISTINCT NULLIF(r.context ->> 'seller_id', '') AS seller,
                   NULLIF(r.context ->> 'category', '') AS category
            FROM app.review_cases c
            JOIN ml.v_risk_orders_for_web r
              ON r.prediction_id = c.prediction_id AND r.order_id = c.order_id
        """
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            rows = connection.execute(sql).fetchall()
        return {
            "sellers": tuple(sorted({str(row["seller"]) for row in rows if row["seller"]})),
            "categories": tuple(sorted({str(row["category"]) for row in rows if row["category"]})),
        }

    @staticmethod
    def _where_clause(filters: QueueFilters) -> tuple[str, dict[str, Any], str | None]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        matched_item_id: str | None = None
        if filters.level is not None:
            clauses.append("r.risk_level = %(level)s")
            params["level"] = filters.level
        if filters.status == "OPEN":
            clauses.append("c.status IN ('PENDING', 'IN_PROGRESS')")
        else:
            clauses.append("c.status = %(status)s")
            params["status"] = filters.status
        if filters.assignee == "none":
            clauses.append("a.assignee_id IS NULL")
        elif filters.assignee is not None:
            clauses.append("a.assignee_id = %(assignee)s")
            params["assignee"] = filters.assignee
        if filters.score_min is not None:
            clauses.append("r.risk_score >= %(score_min)s")
            params["score_min"] = filters.score_min
        if filters.score_max is not None:
            clauses.append("r.risk_score <= %(score_max)s")
            params["score_max"] = filters.score_max
        if filters.queued_from is not None:
            clauses.append("cycle.started_at >= %(queued_from)s")
            params["queued_from"] = filters.queued_from
        if filters.queued_to is not None:
            clauses.append("cycle.started_at <= %(queued_to)s")
            params["queued_to"] = filters.queued_to
        if filters.seller is not None:
            clauses.append("r.context ->> 'seller_id' = %(seller)s")
            params["seller"] = filters.seller
        if filters.category is not None:
            clauses.append("r.context ->> 'category' = %(category)s")
            params["category"] = filters.category
        if filters.outcome is not None:
            prefix, value = filters.outcome.split(":", 1)
            field = "c.outcome" if prefix == "O" else "c.skip_reason"
            clauses.append(f"{field} = %(outcome)s")
            params["outcome"] = value
        if filters.sla == "over":
            clauses.append("cycle.sla_due_at < now()")
        elif filters.sla == "soon":
            clauses.append("cycle.sla_due_at >= now()")
            clauses.append(
                "cycle.sla_due_at <= now() + make_interval(hours => (SELECT value::int FROM app.parameters WHERE param_key='soon_hours' AND effective_at <= now() ORDER BY effective_at DESC, version DESC LIMIT 1))"
            )
        elif filters.sla == "esc":
            clauses.append(
                "c.original_queued_at <= now() - make_interval(days => (SELECT value::int FROM app.parameters WHERE param_key='aging_days' AND effective_at <= now() ORDER BY effective_at DESC, version DESC LIMIT 1))"
            )
        elif filters.sla == "stale":
            clauses.append("c.status = 'IN_PROGRESS'")
            clauses.append(
                "c.updated_at <= now() - make_interval(hours => (SELECT value::int FROM app.parameters WHERE param_key='stale_hours' AND effective_at <= now() ORDER BY effective_at DESC, version DESC LIMIT 1))"
            )
        if filters.needs_decision is not None:
            decision_exists = "EXISTS (SELECT 1 FROM app.manager_decisions d WHERE d.case_id = c.case_id AND (d.cycle_id = cycle.cycle_id OR d.cycle_id IS NULL))"
            clauses.append(
                f"(c.status IN ('COMPLETED', 'SKIPPED') AND NOT {decision_exists})"
                if filters.needs_decision
                else f"NOT (c.status IN ('COMPLETED', 'SKIPPED') AND NOT {decision_exists})"
            )
        if filters.query is not None:
            if PRODUCT_ITEM_ID.fullmatch(filters.query):
                clauses.append(
                    "EXISTS (SELECT 1 FROM ml.v_risk_items_for_web i "
                    "WHERE i.prediction_id=c.prediction_id AND i.order_id=c.order_id "
                    "AND i.product_item_id=%(product_item_id)s)"
                )
                params["product_item_id"] = filters.query
                matched_item_id = filters.query
            else:
                clauses.append("c.order_id LIKE %(order_prefix)s")
                params["order_prefix"] = f"{filters.query}%"
        return (f"WHERE {' AND '.join(clauses)}" if clauses else "", params, matched_item_id)

    @staticmethod
    def _to_order(row: dict[str, Any], matched_item_id: str | None) -> QueueOrder:
        return QueueOrder(
            order_id=str(row["order_id"]),
            score=float(row["risk_score"]),
            level=str(row["risk_level"]),
            status=str(row["status"]),
            assignee_id=str(row["assignee_id"]) if row["assignee_id"] else None,
            assignee_name=row["assignee_name"],
            queued_at=row["original_queued_at"],
            sla_due_at=row["sla_due_at"],
            row_version=int(row["row_version"]),
            matched_item_id=matched_item_id,
        )

    @staticmethod
    def _require_row(row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            raise RuntimeError("Queue count query returned no row")
        return row

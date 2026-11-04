"""PostgreSQL order-grain projection for the Risk Queue."""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.application.queue import QueueOrder, QueuePage
from hidden_dissatisfaction.domain.case_metrics import MetricParameters, case_metrics
from hidden_dissatisfaction.domain.queue import PRODUCT_ITEM_ID, QueueFilters


class PostgresRiskOrderQuery:
    """Execute the Queue read model without exposing persistence rows to HTTP."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def list_orders(self, filters: QueueFilters) -> QueuePage:
        return self._list_orders(filters)

    def get_order(self, order_id: str) -> QueueOrder | None:
        page = self._list_orders(QueueFilters(limit=1), exact_order_id=order_id)
        return page.items[0] if page.items else None

    def _list_orders(self, filters: QueueFilters, exact_order_id: str | None = None) -> QueuePage:
        where, params, matched_item_id = self._where_clause(filters, exact_order_id)
        order_by = {
            "priority": "r.risk_score DESC, cycle.sla_due_at ASC NULLS LAST, c.original_queued_at ASC, c.order_id ASC",
            "sla": "cycle.sla_due_at ASC NULLS LAST, r.risk_score DESC, c.order_id ASC",
            "aging": "c.original_queued_at ASC, r.risk_score DESC, c.order_id ASC",
        }[filters.sort]
        projection = """
            FROM app.review_cases c
            JOIN ml.v_risk_orders_for_web r
              ON r.prediction_id = c.prediction_id AND r.order_id = c.order_id
            JOIN ml.v_risk_items_for_web risk_item
              ON risk_item.prediction_id = r.prediction_id
             AND risk_item.order_id = r.order_id
             AND risk_item.product_item_id = r.top_product_item_id
            LEFT JOIN app.assignments a ON a.case_id = c.case_id AND a.released_at IS NULL
            LEFT JOIN app.users u ON u.user_id = a.assignee_id
            LEFT JOIN LATERAL (
                SELECT y.cycle_id, y.started_at,
                       COALESCE((SELECT a.sla_due_at FROM app.sla_adjustments a
                                 WHERE a.cycle_id = y.cycle_id
                                 ORDER BY a.adjustment_id DESC LIMIT 1), y.sla_due_at) AS sla_due_at
                FROM app.review_cycles y
                WHERE y.case_id = c.case_id
                ORDER BY y.cycle_no DESC LIMIT 1
            ) cycle ON TRUE
        """
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            now_row = connection.execute("SELECT CURRENT_TIMESTAMP AS now").fetchone()
            assert now_row is not None
            now = now_row["now"]
            params["as_of"] = now
            values = connection.execute(
                """SELECT DISTINCT ON (param_key) param_key, value
                FROM app.parameters WHERE effective_at <= %(now)s
                ORDER BY param_key, effective_at DESC, version DESC""",
                {"now": now},
            ).fetchall()
            pv = {r["param_key"]: r["value"] for r in values}
            metric_params = MetricParameters(
                int(pv.get("soon_hours", 24)),
                int(pv.get("aging_days", 3)),
                int(pv.get("stale_hours", 24)),
            )
            total = connection.execute(
                f"SELECT count(*) AS total {projection} {where}", params
            ).fetchone()
            rows = connection.execute(
                f"""
                SELECT c.order_id, r.risk_score, r.risk_level, c.status, a.assignee_id,
                       u.full_name AS assignee_name, cycle.started_at AS queued_at, c.original_queued_at,
                        cycle.sla_due_at, c.row_version, c.outcome, c.skip_reason, c.updated_at,
                        r.top_factors, r.items_count,
                        COALESCE((SELECT count(*)::int FROM app.contact_attempts ca
                                  WHERE ca.cycle_id = cycle.cycle_id), 0) AS contact_count,
                       jsonb_build_object(
                         'product_item_id', risk_item.product_item_id,
                         'risk_score', risk_item.risk_score,
                         'risk_level', risk_item.risk_level,
                         'top_factors', risk_item.top_factors,
                         'synthetic_data_flag', risk_item.synthetic,
                         'model_version', risk_item.model_version,
                         'category', risk_item.context ->> 'category',
                         'data_source', CASE WHEN risk_item.synthetic
                           THEN 'synthetic_v1' ELSE 'olist_order_items' END
                       ) AS top_item
                {projection} {where}
                ORDER BY {order_by}
                LIMIT %(limit)s OFFSET %(offset)s
                """,
                params | {"limit": filters.limit, "offset": filters.offset},
            ).fetchall()
        return QueuePage(
            items=tuple(self._to_order(row, matched_item_id, now, metric_params) for row in rows),
            total=int(self._require_row(total)["total"]),
            limit=filters.limit,
            offset=filters.offset,
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
    def _where_clause(
        filters: QueueFilters, exact_order_id: str | None = None
    ) -> tuple[str, dict[str, Any], str | None]:
        clauses: list[str] = []
        params: dict[str, Any] = {}
        matched_item_id: str | None = None
        if exact_order_id is not None:
            clauses.append("c.order_id = %(exact_order_id)s")
            params["exact_order_id"] = exact_order_id
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
            clauses.append("cycle.sla_due_at < %(as_of)s")
        elif filters.sla == "soon":
            clauses.append("cycle.sla_due_at >= %(as_of)s")
            clauses.append(
                "cycle.sla_due_at <= %(as_of)s + make_interval(hours => (SELECT value::int FROM app.parameters WHERE param_key='soon_hours' AND effective_at <= %(as_of)s ORDER BY effective_at DESC, version DESC LIMIT 1))"
            )
        elif filters.sla == "esc":
            clauses.append(
                "c.original_queued_at <= %(as_of)s - make_interval(days => (SELECT value::int FROM app.parameters WHERE param_key='aging_days' AND effective_at <= %(as_of)s ORDER BY effective_at DESC, version DESC LIMIT 1))"
            )
        elif filters.sla == "stale":
            clauses.append("c.status = 'IN_PROGRESS'")
            clauses.append(
                "c.updated_at <= %(as_of)s - make_interval(hours => (SELECT value::int FROM app.parameters WHERE param_key='stale_hours' AND effective_at <= %(as_of)s ORDER BY effective_at DESC, version DESC LIMIT 1))"
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
    def _to_order(
        row: dict[str, Any], matched_item_id: str | None, now: Any, params: MetricParameters
    ) -> QueueOrder:
        metrics = case_metrics(
            status=row["status"],
            now=now,
            cycle_started_at=row["queued_at"],
            original_queued_at=row["original_queued_at"],
            sla_due_at=row["sla_due_at"],
            updated_at=row["updated_at"],
            params=params,
        )
        top_item = dict(row["top_item"] or {})
        top_item["data_source"] = (
            "synthetic_v1" if top_item.get("synthetic_data_flag") else "olist_order_items"
        )
        top_item.setdefault("category", None)
        return QueueOrder(
            order_id=str(row["order_id"]),
            risk_score=float(row["risk_score"]),
            risk_level=str(row["risk_level"]),
            status=str(row["status"]),
            assignee_id=str(row["assignee_id"]) if row["assignee_id"] else None,
            assignee_name=row["assignee_name"],
            queued_at=row["queued_at"],
            sla_due_at=row["sla_due_at"],
            row_version=int(row["row_version"]),
            original_queued_at=row["original_queued_at"],
            matched_item_id=matched_item_id,
            top_item=top_item,
            top_factors=tuple(row["top_factors"] or ()),
            items_count=int(row["items_count"]),
            outcome=row["outcome"],
            skip_reason=row["skip_reason"],
            self_claim_allowed=row["status"] == "PENDING" and row["risk_level"] != "HIGH",
            contact_count=int(row["contact_count"]),
            **{
                k: metrics[k]
                for k in (
                    "sla_state",
                    "sla_hours_left",
                    "aging_hours",
                    "total_aging_hours",
                    "is_escalated",
                    "is_stale",
                )
            },
        )

    @staticmethod
    def _require_row(row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            raise RuntimeError("Queue count query returned no row")
        return row

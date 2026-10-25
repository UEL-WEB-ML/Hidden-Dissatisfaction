"""PostgreSQL read models for Order Detail, Dashboard and Audit History (P9.3, P9.8)."""

from datetime import datetime, timedelta
from typing import Any

import psycopg
from psycopg.rows import dict_row

from hidden_dissatisfaction.domain.case_metrics import (
    MetricParameters,
    build_dashboard,
    case_metrics,
)
from hidden_dissatisfaction.domain.workflow import CaseNotFoundError

_CASE_ROWS = """
    SELECT c.case_id, c.order_id, c.status, c.assignee_id, u.full_name AS assignee_name,
           c.original_queued_at, c.updated_at, c.outcome, c.skip_reason, c.close_note, c.closed_at,
           c.reopen_count, c.cycle_no, c.row_version, r.risk_score::float AS score,
           r.risk_level AS level, r.context ->> 'seller_id' AS seller,
           r.context ->> 'category' AS category,
           cy.cycle_id, cy.started_at AS cycle_started_at, cy.sla_due_at,
           (SELECT count(*)::int FROM app.contact_attempts a WHERE a.case_id = c.case_id) AS contact_total,
           EXISTS (SELECT 1 FROM app.contact_attempts a
                   WHERE a.case_id = c.case_id AND a.contact_result = 'REACHED') AS reached,
           (SELECT min(a.created_at) FROM app.contact_attempts a
             WHERE a.case_id = c.case_id AND a.created_at >= cy.started_at) AS cycle_first_contact_at,
           EXISTS (SELECT 1 FROM app.manager_decisions d
                   WHERE d.case_id = c.case_id AND d.cycle_id IS NOT DISTINCT FROM cy.cycle_id)
             AS has_decision
    FROM app.review_cases c
    JOIN ml.v_risk_orders_for_web r ON r.prediction_id = c.prediction_id AND r.order_id = c.order_id
    LEFT JOIN app.users u ON u.user_id = c.assignee_id
    LEFT JOIN LATERAL (
        SELECT cycle_id, started_at, sla_due_at FROM app.review_cycles
        WHERE case_id = c.case_id ORDER BY cycle_no DESC LIMIT 1
    ) cy ON TRUE
"""


def _metric_params(conn: psycopg.Connection[Any], now: datetime) -> MetricParameters:
    def value(key: str) -> int:
        row = conn.execute(
            """SELECT value FROM app.parameters WHERE param_key = %s AND effective_at <= %s
               ORDER BY effective_at DESC, version DESC LIMIT 1""",
            (key, now),
        ).fetchone()
        if row is None:
            raise LookupError(f"missing parameter {key}")
        return int(row["value"])

    return MetricParameters(value("soon_hours"), value("aging_days"), value("stale_hours"))


class PostgresCaseReads:
    """Read-only projections; Detail never selects review text or post-prediction features."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def detail(self, order_id: str, now: datetime, include_audit: bool) -> dict[str, Any]:
        """Return the full Order Detail payload; audit events only for Managers."""
        with self._connect() as conn:
            row = conn.execute(_CASE_ROWS + " WHERE c.order_id = %s", (order_id,)).fetchone()
            if row is None:
                raise CaseNotFoundError(order_id)
            params = _metric_params(conn, now)
            order = conn.execute(
                """SELECT r.*, r.risk_score::float AS score_f FROM ml.v_risk_orders_for_web r
                   WHERE r.prediction_id = (SELECT prediction_id FROM app.review_cases WHERE order_id=%s)
                     AND r.order_id = %s""",
                (order_id, order_id),
            ).fetchone()
            items = conn.execute(
                """SELECT i.product_item_id, i.risk_score::float AS risk_score, i.risk_level,
                          i.top_factors, i.synthetic AS synthetic_data_flag, i.context,
                          i.model_version, i.predicted_at,
                          CASE WHEN i.synthetic THEN 'synthetic_v1' ELSE 'olist_order_items' END AS data_source
                   FROM ml.v_risk_items_for_web i
                   WHERE i.prediction_id = (SELECT prediction_id FROM app.review_cases WHERE order_id=%s)
                     AND i.order_id = %s
                   ORDER BY i.risk_score DESC, i.product_item_id""",
                (order_id, order_id),
            ).fetchall()
            cycles = conn.execute(
                """SELECT y.cycle_no, y.started_at, y.ended_at, y.parameter_version,
                          (SELECT count(*)::int FROM app.contact_attempts a WHERE a.cycle_id = y.cycle_id)
                            AS contact_count
                   FROM app.review_cycles y WHERE y.case_id = %s ORDER BY y.cycle_no""",
                (row["case_id"],),
            ).fetchall()
            contacts = conn.execute(
                """SELECT a.attempt_id AS contact_id, y.cycle_no, a.attempt_no,
                          a.attempted_at AS contacted_at, a.channel AS method, a.contact_result AS result,
                          a.note, a.next_contact_date, a.evidence_ref, a.created_by,
                          cu.full_name AS created_by_name,
                          COALESCE((SELECT jsonb_agg(jsonb_build_object(
                                'file_id', e.metadata ->> 'upload_id',
                                'file_name', e.metadata ->> 'file_name',
                                'file_type', e.content_type,
                                'file_size', (e.metadata ->> 'file_size')::int,
                                'url', '/api/v1/files/' || (e.metadata ->> 'upload_id')))
                             FROM app.contact_evidence e WHERE e.attempt_id = a.attempt_id), '[]') AS evidence
                   FROM app.contact_attempts a
                   JOIN app.users cu ON cu.user_id = a.created_by
                   LEFT JOIN app.review_cycles y ON y.cycle_id = a.cycle_id
                   WHERE a.case_id = %s ORDER BY a.created_at, a.attempt_no""",
                (row["case_id"],),
            ).fetchall()
            comments = conn.execute(
                """SELECT m.created_at, m.author_id, au.full_name AS author_name,
                          au.role AS author_role, m.body AS text
                   FROM app.case_comments m JOIN app.users au ON au.user_id = m.author_id
                   WHERE m.case_id = %s ORDER BY m.created_at""",
                (row["case_id"],),
            ).fetchall()
            decisions = conn.execute(
                """SELECT d.created_at, d.decided_by AS actor_id, du.full_name AS actor_name,
                          y.cycle_no, d.decision, d.rationale AS reason, d.next_step,
                          d.next_step_assignee_id, nu.full_name AS next_step_assignee_name,
                          d.due_date, d.note
                   FROM app.manager_decisions d
                   JOIN app.users du ON du.user_id = d.decided_by
                   LEFT JOIN app.users nu ON nu.user_id = d.next_step_assignee_id
                   LEFT JOIN app.review_cycles y ON y.cycle_id = d.cycle_id
                   WHERE d.case_id = %s ORDER BY d.created_at DESC""",
                (row["case_id"],),
            ).fetchall()
            history = conn.execute(
                """SELECT e.created_at, COALESCE(au.full_name, 'System') AS actor_name,
                          e.event_type, e.old_value, e.new_value
                   FROM app.audit_events e LEFT JOIN app.users au ON au.user_id = e.actor_id
                   WHERE e.case_id = %s AND e.event_type IN
                     ('CLAIM','ASSIGN','REASSIGN','STATUS','SKIP','REOPEN','OVERRIDE','QUEUE_SEED')
                   ORDER BY e.created_at, e.event_id""",
                (row["case_id"],),
            ).fetchall()
            model_notes = conn.execute(
                """SELECT e.created_at, au.full_name AS actor_name, e.reason AS note
                   FROM app.audit_events e JOIN app.users au ON au.user_id = e.actor_id
                   WHERE e.case_id = %s AND e.event_type = 'MODEL_NOTE' ORDER BY e.created_at""",
                (row["case_id"],),
            ).fetchall()
            audit = (
                conn.execute(
                    """SELECT e.created_at, e.provenance AS actor_kind, e.actor_id,
                              au.full_name AS actor_name, e.order_id, e.event_type, e.old_value,
                              e.new_value, e.reason
                       FROM app.audit_events e LEFT JOIN app.users au ON au.user_id = e.actor_id
                       WHERE e.case_id = %s ORDER BY e.created_at DESC, e.event_id DESC""",
                    (row["case_id"],),
                ).fetchall()
                if include_audit
                else None
            )
            seller_open = conn.execute(
                _CASE_ROWS.replace("SELECT c.case_id", "SELECT count(*) OVER () AS n, c.case_id", 1)
                + " WHERE c.status IN ('PENDING','IN_PROGRESS') AND r.context ->> 'seller_id' = %s "
                "LIMIT 1",
                (row["seller"],),
            ).fetchone()
        if order is None:
            raise CaseNotFoundError(order_id)
        metrics = case_metrics(
            status=row["status"],
            now=now,
            cycle_started_at=row["cycle_started_at"],
            original_queued_at=row["original_queued_at"],
            sla_due_at=row["sla_due_at"],
            updated_at=row["updated_at"],
            params=params,
        )
        current_decision = decisions[0] if decisions else None
        return {
            "order": {
                "order_id": order_id,
                "case_id": str(row["case_id"]),
                "risk_score": row["score"],
                "risk_level": row["level"],
                "aggregation_rule": (
                    order["aggregation_rule"] if "aggregation_rule" in order else "max-v1"
                ),
                "top_factors": order["top_factors"] or [],
                "model_version": order["model_version"],
                "predicted_at": (
                    order["predicted_at"] if "predicted_at" in order else order["scored_at"]
                ),
                "threshold_version": order["threshold_version"],
                "items_count": order["item_count"],
                "top_item": items[0] if items else None,
                "has_synthetic_item": any(i["synthetic_data_flag"] for i in items),
                "items": items,
                "seller_id": row["seller"],
                "category": row["category"],
                "cycle_no": row["cycle_no"],
                "queued_at": row["cycle_started_at"],
                "original_queued_at": row["original_queued_at"],
                "status": row["status"],
                "self_claim_allowed": row["status"] == "PENDING" and row["level"] != "HIGH",
                "assignee_id": str(row["assignee_id"]) if row["assignee_id"] else None,
                "assignee_name": row["assignee_name"],
                "outcome": row["outcome"],
                "skip_reason": row["skip_reason"],
                "updated_at": row["updated_at"],
                "closed_at": row["closed_at"],
                "reopen_count": row["reopen_count"],
                "sla_due_at": (
                    row["sla_due_at"] if row["status"] in ("PENDING", "IN_PROGRESS") else None
                ),
                "contact_count": cycles[-1]["contact_count"] if cycles else 0,
                "needs_decision": row["status"] in ("COMPLETED", "SKIPPED")
                and not row["has_decision"],
                **metrics,
            },
            "cycles": cycles,
            "contacts": contacts,
            "comments": comments,
            "decisions": decisions,
            "next_step": (
                {
                    k: current_decision[k]
                    for k in (
                        "decision",
                        "reason",
                        "next_step",
                        "next_step_assignee_id",
                        "next_step_assignee_name",
                        "due_date",
                    )
                }
                | {
                    "decided_by": current_decision["actor_name"],
                    "decided_at": current_decision["created_at"],
                }
                if current_decision
                else None
            ),
            "status_history": history,
            "model_notes": model_notes,
            "audit_events": audit,
            "seller_open_count": int(seller_open["n"]) if seller_open else 0,
        }

    def dashboard(
        self,
        now: datetime,
        *,
        days: int | None,
        level: str | None,
        seller: str | None,
        category: str | None,
        assignee: str | None,
        status: str | None,
        product_item: str | None,
        view: str,
    ) -> dict[str, Any]:
        """Aggregate the filtered cases; ``view=product`` adds item-grain counts."""
        since = now - timedelta(days=days) if days else None
        clauses: list[str] = ["TRUE"]
        args: dict[str, Any] = {"since": since}
        if since:
            clauses.append("c.original_queued_at >= %(since)s")
        for column, key, value in (
            ("r.risk_level", "level", level),
            ("r.context ->> 'seller_id'", "seller", seller),
            ("r.context ->> 'category'", "category", category),
        ):
            if value:
                clauses.append(f"{column} = %({key})s")
                args[key] = value
        if assignee:
            clauses.append("c.assignee_id = %(assignee)s")
            args["assignee"] = assignee
        if status:
            clauses.append(
                "c.status IN ('PENDING','IN_PROGRESS')"
                if status == "OPEN"
                else "c.status = %(status)s"
            )
            args["status"] = status
        if product_item:
            clauses.append(
                "EXISTS (SELECT 1 FROM ml.v_risk_items_for_web i WHERE i.prediction_id=c.prediction_id "
                "AND i.order_id=c.order_id AND i.product_item_id = %(product_item)s)"
            )
            args["product_item"] = product_item
        where = " AND ".join(clauses)
        with self._connect() as conn:
            params = _metric_params(conn, now)
            rows = conn.execute(_CASE_ROWS + f" WHERE {where}", args).fetchall()
            specialists = conn.execute(
                """WITH cap AS (SELECT value::int AS v FROM app.parameters WHERE param_key='capacity'
                                  AND effective_at <= %(now)s ORDER BY effective_at DESC, version DESC LIMIT 1)
                   SELECT u.user_id, u.full_name, count(a.assignment_id)::int AS active_count,
                          (SELECT v FROM cap) AS capacity,
                          GREATEST((SELECT v FROM cap) - count(a.assignment_id)::int, 0) AS slots_left
                   FROM app.users u LEFT JOIN app.assignments a
                     ON a.assignee_id = u.user_id AND a.released_at IS NULL
                   WHERE u.is_active AND u.role = 'SPECIALIST' GROUP BY u.user_id ORDER BY u.full_name""",
                {"now": now},
            ).fetchall()
            overrides = conn.execute(
                """SELECT e.created_at, e.event_type, e.order_id, au.full_name AS actor_name, e.reason
                   FROM app.audit_events e LEFT JOIN app.users au ON au.user_id = e.actor_id
                   WHERE e.event_type IN ('ASSIGN','REASSIGN','REOPEN','OVERRIDE','PARAMETER_CHANGE')
                   ORDER BY e.created_at DESC, e.event_id DESC LIMIT 5"""
            ).fetchall()
            product = None
            if view == "product":
                order_ids = [r["order_id"] for r in rows]
                items = conn.execute(
                    """SELECT i.product_item_id, i.order_id, i.context ->> 'category' AS category,
                              i.risk_score::float AS risk_score, i.risk_level,
                              i.synthetic AS synthetic_data_flag, c.status AS order_status,
                              i.top_factors ->> 0 AS top_factor
                       FROM ml.v_risk_items_for_web i
                       JOIN app.review_cases c ON c.prediction_id = i.prediction_id AND c.order_id = i.order_id
                       WHERE i.order_id = ANY(%s) ORDER BY i.risk_score DESC, i.product_item_id""",
                    (order_ids,),
                ).fetchall()
                categories: dict[str, dict[str, Any]] = {}
                for item in items:
                    key = item["category"] or "unknown"
                    bucket = categories.setdefault(
                        key, {"key": key, "total": 0, "high": 0, "open": 0, "related": []}
                    )
                    bucket["total"] += 1
                    bucket["high"] += item["risk_level"] == "HIGH"
                    bucket["open"] += item["order_status"] in ("PENDING", "IN_PROGRESS")
                product = {
                    "totals": {
                        "total_items": len(items),
                        **{
                            lv: sum(i["risk_level"] == lv for i in items)
                            for lv in ("HIGH", "MEDIUM", "LOW")
                        },
                        "synthetic": sum(i["synthetic_data_flag"] for i in items),
                        "orders": len(order_ids),
                    },
                    "by_category": sorted(
                        categories.values(), key=lambda b: (-b["high"], b["key"])
                    )[:10],
                    "top_items": items[:10],
                }
        result = build_dashboard(
            [dict(r) for r in rows],
            [dict(s) for s in specialists],
            [dict(o) for o in overrides],
            now=now,
            params=params,
            since=since,
        )
        result["view"] = view
        if product is not None:
            result["product"] = product
        return result

    def audit_events(
        self,
        *,
        event_type: str | None,
        actor_id: str | None,
        order_id: str | None,
        override_only: bool,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        """Read-only, stable (created_at, event_id) ordering with an unfiltered total."""
        clauses: list[str] = ["TRUE"]
        args: dict[str, Any] = {"limit": limit, "offset": offset}
        if event_type:
            clauses.append("e.event_type = %(event_type)s")
            args["event_type"] = event_type
        if actor_id:
            clauses.append("e.actor_id = %(actor_id)s")
            args["actor_id"] = actor_id
        if order_id:
            clauses.append("e.order_id LIKE %(order_id)s")
            args["order_id"] = f"{order_id}%"
        if override_only:
            clauses.append("e.event_type IN ('REASSIGN','REOPEN','OVERRIDE')")
        where = " AND ".join(clauses)
        with self._connect() as conn:
            total = conn.execute(
                f"SELECT count(*)::int AS n FROM app.audit_events e WHERE {where}", args
            ).fetchone()
            everything = conn.execute("SELECT count(*)::int AS n FROM app.audit_events").fetchone()
            rows = conn.execute(
                f"""SELECT e.event_id, e.created_at, e.provenance AS actor_kind, e.actor_id,
                           au.full_name AS actor_name, e.order_id, e.event_type, e.old_value,
                           e.new_value, e.reason,
                           CASE WHEN c.case_id IS NULL THEN NULL ELSE jsonb_build_object(
                             'status', c.status, 'risk_level', r.risk_level,
                             'assignee_name', cu.full_name,
                             'event_count', (SELECT count(*) FROM app.audit_events x WHERE x.case_id = c.case_id),
                             'has_override', EXISTS (SELECT 1 FROM app.audit_events x
                                WHERE x.case_id = c.case_id AND x.event_type = 'OVERRIDE')) END AS "order"
                    FROM app.audit_events e
                    LEFT JOIN app.users au ON au.user_id = e.actor_id
                    LEFT JOIN app.review_cases c ON c.case_id = e.case_id
                    LEFT JOIN ml.v_risk_orders_for_web r
                      ON r.prediction_id = c.prediction_id AND r.order_id = c.order_id
                    LEFT JOIN app.users cu ON cu.user_id = c.assignee_id
                    WHERE {where}
                    ORDER BY e.created_at DESC, e.event_id DESC LIMIT %(limit)s OFFSET %(offset)s""",
                args,
            ).fetchall()
        assert total is not None and everything is not None
        return {"items": rows, "total": total["n"], "all_total": everything["n"]}

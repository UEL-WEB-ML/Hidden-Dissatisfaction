"""Seed Olist-sized cases into a DISPOSABLE database and time Queue/Dashboard reads.

Usage: bench_queue.py SETUP_DSN RUNTIME_DSN [ORDERS]. Never point this at a shared database:
ml.* and audit rows are immutable, so the seeded data cannot be removed.
"""

import sys
import time
from datetime import UTC, datetime

import psycopg

from hidden_dissatisfaction.domain.queue import QueueFilters
from hidden_dissatisfaction.infrastructure.postgres_case_reads import PostgresCaseReads
from hidden_dissatisfaction.infrastructure.postgres_risk_queue import PostgresRiskOrderQuery

setup_dsn, runtime_dsn = sys.argv[1], sys.argv[2]
orders = int(sys.argv[3]) if len(sys.argv) > 3 else 100_000

with psycopg.connect(setup_dsn, autocommit=True) as conn:
    row = conn.execute("SELECT prediction_id FROM ml.predictions WHERE state='ACTIVE'").fetchone()
    if row is None:
        sys.exit("no ACTIVE prediction; run the integration tests once first")
    pid = row[0]
    have = conn.execute("SELECT count(*) FROM app.review_cases").fetchone()[0]  # type: ignore[index]
    need = max(orders - have, 0)
    if need:
        conn.execute(
            """INSERT INTO ml.item_prediction_scores(prediction_id, order_id, order_item_id,
                   product_item_id, score, risk_context)
               SELECT %(p)s, o, '1', o || '-1', round(random()::numeric, 10),
                      jsonb_build_object('seller_id', 's' || (abs(hashtext(o)) %% 3000),
                                         'category', 'c' || (abs(hashtext(o)) %% 70))
               FROM (SELECT md5('bench' || g::text) AS o FROM generate_series(1, %(n)s) g) t""",
            {"p": pid, "n": need},
        )
        conn.execute(
            """INSERT INTO ml.order_prediction_scores(prediction_id, order_id, score, aggregation_rule,
                   top_product_item_id, top_item_score, item_count, item_value, risk_context)
               SELECT prediction_id, order_id, score, 'max-v1', product_item_id, score, 1, 10, risk_context
               FROM ml.item_prediction_scores WHERE prediction_id=%s AND order_id IN
                 (SELECT md5('bench' || g::text) FROM generate_series(1, %s) g)""",
            (pid, need),
        )
        conn.execute(
            """INSERT INTO app.review_cases(order_id, prediction_id, aggregation_rule, status,
                   original_queued_at)
               SELECT order_id, prediction_id, 'max-v1',
                      (ARRAY['PENDING','PENDING','PENDING','IN_PROGRESS','COMPLETED'])[1 + abs(hashtext(order_id)) %% 5],
                      now() - (abs(hashtext(order_id)) %% 2000) * interval '1 hour'
               FROM ml.order_prediction_scores WHERE prediction_id=%s AND order_id IN
                 (SELECT md5('bench' || g::text) FROM generate_series(1, %s) g)""",
            (pid, need),
        )
        conn.execute(
            """INSERT INTO app.review_cycles(case_id, cycle_no, started_at, sla_due_at)
               SELECT c.case_id, 1, c.original_queued_at, c.original_queued_at + interval '24 hours'
               FROM app.review_cases c WHERE NOT EXISTS
                 (SELECT 1 FROM app.review_cycles y WHERE y.case_id = c.case_id)"""
        )
        conn.execute("ANALYZE")
    total = conn.execute("SELECT count(*) FROM app.review_cases").fetchone()[0]  # type: ignore[index]
print(f"cases in database: {total}")


def timed(label: str, call: object) -> None:
    started = time.perf_counter()
    result = call()  # type: ignore[operator]
    print(f"{label:<34}{(time.perf_counter() - started) * 1000:9.1f} ms  {result}")


queue, reads = PostgresRiskOrderQuery(runtime_dsn), PostgresCaseReads(runtime_dsn)
now = datetime.now(UTC)
timed("queue priority page 1", lambda: queue.list_orders(QueueFilters(limit=20)).total)
timed(
    "queue priority page 500",
    lambda: len(queue.list_orders(QueueFilters(limit=20, offset=9980)).items),
)
timed("queue level=HIGH", lambda: queue.list_orders(QueueFilters(level="HIGH", limit=20)).total)
timed("queue sla=over", lambda: queue.list_orders(QueueFilters(sla="over", limit=20)).total)
timed("queue q=prefix", lambda: queue.list_orders(QueueFilters(query="ab", limit=20)).total)
timed("queue seller filter", lambda: queue.list_orders(QueueFilters(seller="s7", limit=20)).total)
timed(
    "queue needs_decision",
    lambda: queue.list_orders(
        QueueFilters(status="COMPLETED", needs_decision=True, limit=20)
    ).total,
)
timed("filter-options", lambda: len(queue.filter_options()["sellers"]))
args = {
    "days": None,
    "level": None,
    "seller": None,
    "category": None,
    "assignee": None,
    "status": None,
    "product_item": None,
    "view": "order",
}
timed("dashboard order view", lambda: reads.dashboard(now, **args)["totals"]["cases"])  # type: ignore[arg-type]
timed("dashboard product view", lambda: reads.dashboard(now, **{**args, "view": "product"})["product"]["totals"]["total_items"])  # type: ignore[arg-type]
timed(
    "audit-events page 1",
    lambda: reads.audit_events(
        event_type=None, actor_id=None, order_id=None, override_only=False, limit=20, offset=0
    )["total"],
)

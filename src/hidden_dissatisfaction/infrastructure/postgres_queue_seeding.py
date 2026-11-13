"""Transactional PostgreSQL queue seeding adapter."""

from __future__ import annotations

from datetime import datetime, timedelta

import psycopg

from hidden_dissatisfaction.application.queue_seeding import SeedSummary


class PostgresQueueSeedStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def seed(self, prediction_id: str, now: datetime) -> SeedSummary:
        created = skipped = 0
        with psycopg.connect(self.dsn) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT order_id, score, risk_level
                        FROM ml.v_queue_seed_orders
                        WHERE prediction_id=%s AND aggregation_rule='max-v1'""",
                        (prediction_id,),
                    )
                    orders = cur.fetchall()
                    for order_id, _score, risk_level in orders:
                        cur.execute(
                            """SELECT COALESCE(value, '48'), version FROM app.parameters
                            WHERE param_key=%s AND effective_at<=%s
                            ORDER BY effective_at DESC, version DESC LIMIT 1""",
                            ("sla_hours_" + str(risk_level).lower(), now),
                        )
                        parameter = cur.fetchone()
                        if parameter is None:
                            raise RuntimeError("effective SLA parameter is missing")
                        hours, parameter_version = int(parameter[0]), parameter[1]
                        cur.execute(
                            """INSERT INTO app.review_cases
                            (order_id,prediction_id,aggregation_rule,original_queued_at)
                            VALUES (%s,%s,'max-v1',%s)
                            ON CONFLICT (order_id) DO NOTHING RETURNING case_id""",
                            (order_id, prediction_id, now),
                        )
                        row = cur.fetchone()
                        if row is None:
                            skipped += 1
                            continue
                        created += 1
                        cur.execute(
                            """INSERT INTO app.review_cycles
                            (case_id,cycle_no,started_at,sla_due_at,parameter_version)
                            VALUES (%s,1,%s,%s,%s)""",
                            (row[0], now, now + timedelta(hours=hours), parameter_version),
                        )
                        cur.execute(
                            """INSERT INTO app.audit_events
                            (case_id,order_id,provenance,event_type,new_value,reason,actor_kind)
                            VALUES (%s,%s,'QUEUE_SEED','QUEUE_SEED','PENDING',%s,'SYSTEM')""",
                            (row[0], order_id, "prediction " + str(prediction_id)),
                        )
        return SeedSummary(created, skipped)


PostgresQueueSeeder = PostgresQueueSeedStore

\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- Chosen from EXPLAIN ANALYZE on ~100k cases (scripts/bench_queue.py): the Queue
-- and Dashboard read paths filter open cases by status and score by cycle.
CREATE INDEX review_cases_status_idx ON app.review_cases(status);
CREATE INDEX review_cases_assignee_open_idx ON app.review_cases(assignee_id) WHERE status = 'IN_PROGRESS';
CREATE INDEX review_cases_queued_idx ON app.review_cases(original_queued_at);
CREATE INDEX manager_decisions_cycle_idx ON app.manager_decisions(case_id, cycle_id);
CREATE INDEX audit_events_order_idx ON app.audit_events(order_id text_pattern_ops);

RESET ROLE;

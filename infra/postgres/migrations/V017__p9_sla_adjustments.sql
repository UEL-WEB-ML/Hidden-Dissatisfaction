\set ON_ERROR_STOP on
SET ROLE hidden_dissatisfaction_owner;

-- review_cycles.sla_due_at is immutable (V008 guard). When an SLA parameter
-- changes, the derived due time of an OPEN cycle is recorded here instead; the
-- latest row wins. Closed cycles and historical events are never rewritten.
CREATE TABLE app.sla_adjustments (
 adjustment_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 cycle_id uuid NOT NULL REFERENCES app.review_cycles(cycle_id),
 sla_due_at timestamptz NOT NULL,
 parameter_id bigint NOT NULL REFERENCES app.parameters(parameter_id),
 applied_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (cycle_id, parameter_id)
);
CREATE INDEX sla_adjustments_cycle_idx ON app.sla_adjustments(cycle_id, adjustment_id DESC);
CREATE TRIGGER sla_adjustments_immutable BEFORE UPDATE OR DELETE ON app.sla_adjustments
  FOR EACH ROW EXECUTE FUNCTION app.p7_workflow_append_only();
GRANT SELECT, INSERT ON app.sla_adjustments TO app_runtime;
GRANT SELECT ON app.sla_adjustments TO reader;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO app_runtime;

RESET ROLE;

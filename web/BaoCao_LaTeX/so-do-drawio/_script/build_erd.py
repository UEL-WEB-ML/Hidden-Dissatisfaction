from pathlib import Path
from dio import D

OUT = Path(__file__).parent / "drawio"
PK, FK, UK = "<b>PK</b> ", "<i>FK</i> ", "<b>UK</b> "

# ---------------- ERD 1: nghiệp vụ xử lý case (schema app) ------------------
d = D("erd-nghiep-vu")
T = d.table
com = T("case_comments", [PK + "comment_id", FK + "case_id", FK + "author_id", "body", "created_at"], 0, 0, 210)
users = T("users", [PK + "user_id : uuid", UK + "username", "password_hash", "full_name", "role", "preferred_language", "is_active", "created_at"], 0, 300, 210)
cases = T("review_cases", [PK + "case_id : uuid", UK + "order_id", FK + "prediction_id", FK + "assignee_id", "status", "cycle_no", "original_queued_at",
                           "outcome", "skip_reason", "closed_at", "reopen_count", "row_version"], 380, 260, 220)
assign = T("assignments", [PK + "assignment_id", FK + "case_id", FK + "assignee_id", "assigned_at", "released_at", "release_reason"], 380, 620, 220)
dec = T("manager_decisions", [PK + "decision_id", FK + "case_id", FK + "cycle_id", FK + "decided_by", "decision", "rationale", "next_step",
                              FK + "next_step_assignee_id", "due_date", "created_at"], 380, 820, 220)
cycles = T("review_cycles", [PK + "cycle_id", FK + "case_id", "cycle_no", "started_at", "ended_at", "reopen_reason", FK + "reopened_by", "sla_due_at",
                             FK + "parameter_bundle_id"], 700, 0, 220)
att = T("contact_attempts", [PK + "attempt_id", FK + "case_id", FK + "cycle_id", FK + "assignment_id", "attempt_no", "attempted_at", "channel",
                             "contact_result", "note", "next_contact_date", FK + "created_by"], 700, 300, 220)
evi = T("contact_evidence", [PK + "evidence_id", FK + "case_id", FK + "attempt_id", "storage_key", "content_type", "metadata", "expires_at", FK + "attached_by"], 1000, 300, 210)
upl = T("evidence_uploads", [PK + "upload_id", FK + "uploaded_by", "storage_key", "file_name", "content_type", "file_size", "attached_at"], 1300, 300, 210)
aud = T("audit_events", [PK + "event_id", FK + "case_id", "order_id", FK + "actor_id", "actor_kind", "provenance", "event_type", "old_value",
                         "new_value", "reason", "created_at"], 1000, 580, 220)
cor = T("audit_corrections", [PK + "correction_id", FK + "event_id", FK + "corrected_by", "correction", "created_at"], 1000, 880, 220)
R = lambda a, b, ex="", pts=None: d.edge(a, b, "", "er", extra=ex, pts=pts)
R(users, cases, "exitX=1;exitY=0.1613;entryX=0;entryY=0.2632;")
R(cases, com, "exitX=0;exitY=0.06;entryX=0.5;entryY=1;", pts=[(105, 277)])
R(users, assign, "exitX=0.5;exitY=1;entryX=0;entryY=0.3151;", pts=[(105, 666)])
R(cases, assign, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
R(cases, cycles, "exitX=1;exitY=0.1015;entryX=0;entryY=0.5485;", pts=[(640, 287), (640, 113)])
R(cases, att, "exitX=1;exitY=0.5;entryX=0;entryY=0.378;")
R(cycles, att, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
R(assign, att, "exitX=1;exitY=0.3973;entryX=0;entryY=0.8496;", pts=[(670, 678), (670, 509)])
R(cases, dec, "exitX=1;exitY=0.9023;entryX=1;entryY=0.3363;", pts=[(640, 500), (640, 896)])
R(att, evi, "exitX=1;exitY=0.3008;entryX=0;entryY=0.3978;")
R(cases, aud, "exitX=0.5;exitY=0;entryX=1;entryY=0.15;", pts=[(490, -40), (1260, -40), (1260, 617)])
R(aud, cor, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
R(users, upl, "exitX=0;exitY=0.8065;entryX=0.5;entryY=1;", pts=[(-30, 450), (-30, 1180), (1405, 1180)])
(OUT / "erd-nghiep-vu.drawio").write_text(d.xml())

# ---------------- ERD 2: dự đoán + tham số ----------------------------------
d = D("erd-du-doan-tham-so")
T = d.table
rel = T("ml.model_releases", [PK + "model_release_id", "release_version", "model_name", "model_version", "model_artifact_uri", "artifact_sha256",
                              "feature_schema_version", "aggregation_rule", "evaluation_status"], 0, 0, 230, "tblml")
thr = T("ml.model_thresholds", ["<b>PK</b>,<i>FK</i> " + "model_release_id", PK + "threshold_version", "medium_from", "high_from", "selection_policy"], 0, 260, 230, "tblml")
pre = T("ml.predictions", [PK + "prediction_id", FK + "model_release_id", FK + "threshold_version", "source_run_id", "input_hash", "scored_at",
                           "state (READY/ACTIVE/...)", "activated_at"], 290, 0, 230, "tblml")
item = T("ml.item_prediction_scores", ["<b>PK</b>,<i>FK</i> " + "prediction_id", PK + "order_id", PK + "order_item_id", "product_item_id", "score", "risk_context",
                                       "top_factors", "synthetic"], 580, 0, 240, "tblml")
order = T("ml.order_prediction_scores", ["<b>PK</b>,<i>FK</i> " + "prediction_id", PK + "order_id", "score (= top item)", "aggregation_rule", FK + "top_product_item_id",
                                         "top_item_score", "item_count", "top_factors"], 580, 230, 240, "tblml")
case = T("app.review_cases", [PK + "case_id", UK + "order_id", FK + "prediction_id", "status", "..."], 290, 260, 230)
cyc = T("app.review_cycles", [PK + "cycle_id", FK + "case_id", "sla_due_at", FK + "parameter_bundle_id"], 290, 420, 230)
pdef = T("app.parameter_definitions", [PK + "param_key", "unit", "min_value", "max_value", "allowed_values", "description"], 0, 450, 230)
par = T("app.parameters", [PK + "parameter_id", FK + "param_key", "version", "value", "effective_at", FK + "actor_id", "reason"], 0, 620, 230)
bun = T("app.parameter_bundles", [PK + "bundle_id", "revision", FK + "parameter_id", FK + "created_by"], 290, 580, 230)
sla = T("app.sla_adjustments", [PK + "adjustment_id", FK + "cycle_id", "sla_due_at", FK + "parameter_id", "applied_at"], 580, 470, 240)
R = lambda a, b, ex="", st="er": d.edge(a, b, "", st, extra=ex)
R(rel, thr, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"); R(thr, pre, "exitX=1;exitY=0.3;entryX=0;entryY=0.7;"); R(rel, pre)
R(pre, item); R(item, order, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"); R(pre, order, "exitX=1;exitY=0.9;entryX=0;entryY=0.3;")
R(pre, case, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;dashed=1;")
R(case, cyc, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
R(pdef, par, "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"); R(par, bun, "exitX=1;exitY=0.3;entryX=0;entryY=0.5;")
R(bun, cyc, "exitX=0.5;exitY=0;entryX=0.5;entryY=1;", "er01"); R(cyc, sla, "exitX=1;exitY=0.5;entryX=0;entryY=0.3;"); R(par, sla, "exitX=1;exitY=0.85;entryX=0.3;entryY=1;")
(OUT / "erd-du-doan-tham-so.drawio").write_text(d.xml())
print("erd done")

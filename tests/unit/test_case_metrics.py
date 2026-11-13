from datetime import UTC, datetime, timedelta
from typing import Any

from hidden_dissatisfaction.domain.case_metrics import (
    MetricParameters,
    build_dashboard,
    case_metrics,
)

NOW = datetime(2026, 10, 25, 12, tzinfo=UTC)
PARAMS = MetricParameters(soon_hours=2, aging_days=2, stale_hours=24)


def metrics(**over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "status": "IN_PROGRESS",
        "now": NOW,
        "cycle_started_at": NOW - timedelta(hours=3),
        "original_queued_at": NOW - timedelta(hours=3),
        "sla_due_at": NOW + timedelta(hours=5),
        "updated_at": NOW - timedelta(hours=1),
        "params": PARAMS,
    }
    return case_metrics(**{**base, **over})


def test_sla_state_boundaries() -> None:
    assert metrics()["sla_state"] == "ok"
    assert metrics(sla_due_at=NOW + timedelta(hours=2))["sla_state"] == "soon"
    assert metrics(sla_due_at=NOW - timedelta(minutes=1))["sla_state"] == "over"
    closed = metrics(status="COMPLETED")
    assert (closed["sla_state"], closed["sla_hours_left"], closed["is_escalated"]) == (
        "none",
        None,
        False,
    )


def test_escalation_and_stale_use_parameter_thresholds() -> None:
    assert metrics(original_queued_at=NOW - timedelta(days=2))["is_escalated"] is True
    assert metrics(original_queued_at=NOW - timedelta(hours=47))["is_escalated"] is False
    assert metrics(updated_at=NOW - timedelta(hours=24))["is_stale"] is True
    assert metrics(status="PENDING", updated_at=NOW - timedelta(days=9))["is_stale"] is False


def row(order: str, level: str, status: str = "PENDING", **over: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "order_id": order,
        "status": status,
        "level": level,
        "score": 0.9 if level == "HIGH" else 0.3,
        "seller": "s1",
        "category": "toys",
        "assignee_id": None,
        "outcome": None,
        "original_queued_at": NOW - timedelta(hours=2),
        "cycle_started_at": NOW - timedelta(hours=2),
        "sla_due_at": NOW + timedelta(hours=1),
        "updated_at": NOW,
        "contact_total": 0,
        "reached": False,
        "cycle_first_contact_at": None,
        "has_decision": False,
    }
    return {**base, **over}


def test_dashboard_totals_reconcile_with_row_filters() -> None:
    rows = [row("a", "HIGH"), row("b", "HIGH"), row("c", "HIGH"), row("d", "LOW", "COMPLETED")]
    out = build_dashboard(rows, [], [], now=NOW, params=PARAMS, since=None)
    assert out["totals"]["cases"] == 4 and out["totals"]["open"] == 3
    assert out["by_level"] == {"HIGH": 3, "MEDIUM": 0, "LOW": 1}
    assert sum(b["count"] for b in out["score_bands"]) == 4
    assert out["totals"]["needs_decision"] == 1
    assert sum(sum(d[lv] for lv in ("HIGH", "MEDIUM", "LOW")) for d in out["trend"]) == 4
    codes = {a["code"] for a in out["actions"]}
    assert {"ASSIGN_HIGH", "DECIDE", "SELLER_HOTSPOT"} <= codes


def test_service_block_counts_contacts_and_sla() -> None:
    contacted = row(
        "a",
        "HIGH",
        "COMPLETED",
        contact_total=2,
        reached=True,
        outcome="HAS_ISSUE",
        cycle_first_contact_at=NOW - timedelta(hours=1),
        has_decision=True,
    )
    out = build_dashboard(
        [contacted, row("b", "HIGH", "IN_PROGRESS")], [], [], now=NOW, params=PARAMS, since=None
    )
    service = out["service"]
    assert (service["contacted"], service["reached"], service["first_in_sla"]) == (1, 1, 1)
    assert service["median_first_contact_hours"] == 1.0
    assert (service["issue_found"], service["issue_followed_up"]) == (1, 1)
    assert service["high_open_not_contacted"] == 1


def test_empty_dashboard_has_null_rates_not_division_errors() -> None:
    out = build_dashboard([], [], [], now=NOW, params=PARAMS, since=None)
    assert out["rates"] == {"closed": None, "overdue": None, "high": None}
    assert out["service"]["median_first_contact_hours"] is None and out["trend"] == []

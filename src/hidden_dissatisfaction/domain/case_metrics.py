"""Pure SLA, aging, stale and Dashboard definitions shared by Queue, Detail and Dashboard."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import median
from typing import Any

OPEN = frozenset({"PENDING", "IN_PROGRESS"})
LEVELS = ("HIGH", "MEDIUM", "LOW")
SCORE_BANDS = ((0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0001))


@dataclass(frozen=True)
class MetricParameters:
    """Operational parameters needed to derive case metrics at one instant."""

    soon_hours: int
    aging_days: int
    stale_hours: int


def _hours(delta: timedelta) -> float:
    return round(delta.total_seconds() / 3600, 2)


def case_metrics(
    *,
    status: str,
    now: datetime,
    cycle_started_at: datetime | None,
    original_queued_at: datetime,
    sla_due_at: datetime | None,
    updated_at: datetime,
    params: MetricParameters,
) -> dict[str, Any]:
    """Derive the Backend-owned fields of the API Order object (API Contract 3.1)."""
    is_open = status in OPEN
    if not is_open or sla_due_at is None:
        sla_state, hours_left = "none", None
    else:
        hours_left = _hours(sla_due_at - now)
        sla_state = (
            "over" if hours_left < 0 else "soon" if hours_left <= params.soon_hours else "ok"
        )
    total_aging = _hours(now - original_queued_at)
    stale = status == "IN_PROGRESS" and now - updated_at >= timedelta(hours=params.stale_hours)
    return {
        "sla_state": sla_state,
        "sla_hours_left": hours_left,
        "aging_hours": _hours(now - cycle_started_at) if cycle_started_at else 0.0,
        "total_aging_hours": total_aging,
        "is_escalated": is_open and total_aging >= params.aging_days * 24,
        "is_stale": stale,
        "stale_hours": _hours(now - updated_at) if stale else None,
    }


def build_dashboard(
    rows: list[dict[str, Any]],
    specialists: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    *,
    now: datetime,
    params: MetricParameters,
    since: datetime | None,
) -> dict[str, Any]:
    """Aggregate already-filtered case rows; the same rows feed ``GET /orders`` filters."""
    metrics = [
        case_metrics(
            status=r["status"],
            now=now,
            cycle_started_at=r["cycle_started_at"],
            original_queued_at=r["original_queued_at"],
            sla_due_at=r["sla_due_at"],
            updated_at=r["updated_at"],
            params=params,
        )
        for r in rows
    ]
    pairs = list(zip(rows, metrics, strict=True))
    is_open = [r["status"] in OPEN for r in rows]
    closed = [r["status"] not in OPEN for r in rows]
    needs = [c and not r["has_decision"] for r, c in zip(rows, closed, strict=True)]
    overdue = [m["sla_state"] == "over" for m in metrics]
    total = len(rows)
    by_status = {
        s: sum(r["status"] == s for r in rows)
        for s in ("PENDING", "IN_PROGRESS", "COMPLETED", "SKIPPED")
    }

    def group(key: str) -> list[dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for r, o in zip(rows, is_open, strict=True):
            bucket = out.setdefault(
                r[key] or "unknown", {"key": r[key] or "unknown", "total": 0, "high": 0, "open": 0}
            )
            bucket["total"] += 1
            bucket["high"] += r["level"] == "HIGH"
            bucket["open"] += o
        return sorted(out.values(), key=lambda b: (-b["high"], -b["total"], b["key"]))[:10]

    by_seller = group("seller")
    overdue_by_assignee: dict[str, int] = {}
    for r, m in pairs:
        if r["assignee_id"] is not None and r["status"] in OPEN and m["sla_state"] == "over":
            key = str(r["assignee_id"])
            overdue_by_assignee[key] = overdue_by_assignee.get(key, 0) + 1
    workload = [
        {
            "user_id": str(s["user_id"]),
            "full_name": s["full_name"],
            "active": s["active_count"],
            "capacity": s["capacity"],
            "overdue": overdue_by_assignee.get(str(s["user_id"]), 0),
        }
        for s in specialists
    ]
    first_contacts = [r for r in rows if r["cycle_first_contact_at"] is not None]
    waits = [_hours(r["cycle_first_contact_at"] - r["cycle_started_at"]) for r in first_contacts]
    unassigned_high = [
        (r, o)
        for r, o in zip(rows, overdue, strict=True)
        if r["level"] == "HIGH" and r["status"] == "PENDING" and r["assignee_id"] is None
    ]
    actions: list[dict[str, Any]] = []
    best = max(
        (s for s in specialists if s["slots_left"]), key=lambda s: s["slots_left"], default=None
    )
    if unassigned_high:
        actions.append(
            {
                "code": "ASSIGN_HIGH",
                "severity": "danger",
                "count": len(unassigned_high),
                "overdue": sum(o for _, o in unassigned_high),
                "suggest": best["full_name"] if best else None,
            }
        )
    for w in workload:
        if w["capacity"] and w["active"] >= w["capacity"] and w["overdue"]:
            actions.append(
                {
                    "code": "REBALANCE",
                    "severity": "warn",
                    **w,
                    "suggest": best["full_name"] if best else None,
                }
            )
    stale_count = sum(m["is_stale"] for m in metrics)
    if stale_count:
        actions.append(
            {"code": "STALE", "severity": "warn", "count": stale_count, "hours": params.stale_hours}
        )
    if sum(needs):
        actions.append({"code": "DECIDE", "severity": "info", "count": sum(needs)})
    # ponytail: hotspot thresholds (>=3 HIGH and >=50%) are fixed until ADR/parameter approval.
    if by_seller and by_seller[0]["key"] != "unknown":
        top = by_seller[0]
        if top["high"] >= 3 and top["high"] / top["total"] >= 0.5:
            actions.append(
                {
                    "code": "SELLER_HOTSPOT",
                    "severity": "warn",
                    "seller_id": top["key"],
                    "high": top["high"],
                    "total": top["total"],
                    "high_total": sum(r["level"] == "HIGH" for r in rows),
                }
            )
    trend: dict[str, dict[str, int]] = {}
    for r in rows:
        day = trend.setdefault(
            r["original_queued_at"].date().isoformat(), {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        )
        day[r["level"]] += 1
    return {
        "as_of": now.isoformat(),
        "from": since.isoformat() if since else None,
        "totals": {
            "cases": total,
            "open": sum(is_open),
            "pending": by_status["PENDING"],
            "in_progress": by_status["IN_PROGRESS"],
            "completed": by_status["COMPLETED"],
            "skipped": by_status["SKIPPED"],
            "overdue": sum(overdue),
            "escalated": sum(m["is_escalated"] for m in metrics),
            "stale": stale_count,
            "needs_decision": sum(needs),
        },
        "rates": {
            "closed": round(sum(closed) / total, 4) if total else None,
            "overdue": round(sum(overdue) / sum(is_open), 4) if sum(is_open) else None,
            "high": round(sum(r["level"] == "HIGH" for r in rows) / total, 4) if total else None,
        },
        "by_level": {lv: sum(r["level"] == lv for r in rows) for lv in LEVELS},
        "score_bands": [
            {"from": lo, "to": min(hi, 1.0), "count": sum(lo <= r["score"] < hi for r in rows)}
            for lo, hi in SCORE_BANDS
        ],
        "by_seller": by_seller,
        "by_category": group("category"),
        "workload": workload,
        "attention": {
            "high_unassigned": len(unassigned_high),
            "overdue": sum(overdue),
            "stale": stale_count,
            "needs_decision": sum(needs),
        },
        "recent_overrides": overrides,
        "service": {
            "cases": total,
            "contacted": sum(r["contact_total"] > 0 for r in rows),
            "reached": sum(bool(r["reached"]) for r in rows),
            "with_first_contact": len(first_contacts),
            "first_in_sla": sum(
                r["sla_due_at"] is not None and r["cycle_first_contact_at"] <= r["sla_due_at"]
                for r in first_contacts
            ),
            "median_first_contact_hours": round(median(waits), 2) if waits else None,
            "issue_found": sum(r["outcome"] == "HAS_ISSUE" for r in rows),
            "issue_followed_up": sum(
                r["outcome"] == "HAS_ISSUE" and r["has_decision"] for r in rows
            ),
            "high_open_not_contacted": sum(
                r["level"] == "HIGH" and o and r["contact_total"] == 0
                for r, o in zip(rows, is_open, strict=True)
            ),
        },
        "actions": actions,
        "trend": [{"date": d, **v} for d, v in sorted(trend.items())],
    }

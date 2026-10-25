from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from hidden_dissatisfaction.domain.workflow import (
    CaseSnapshot,
    WorkflowPolicyError,
    detect_evidence_type,
    validate_assign,
    validate_claim,
    validate_comment,
    validate_contact,
    validate_contact_inputs,
    validate_decision,
    validate_reopen,
)

NOW = datetime(2026, 10, 25, tzinfo=UTC)


def case() -> CaseSnapshot:
    return CaseSnapshot("PENDING", "LOW", None, 0, 3, None, 0)


def test_claim_rejects_high_risk_and_capacity() -> None:
    with pytest.raises(WorkflowPolicyError, match="Manager") as high:
        validate_claim(replace(case(), risk_level="HIGH"), "u1", 0, 5)
    assert high.value.code == "HIGH_RISK_REQUIRES_ASSIGN"
    with pytest.raises(WorkflowPolicyError, match="capacity"):
        validate_claim(case(), "u1", 5, 5)


def test_final_unsuccessful_contact_auto_skips() -> None:
    active = replace(case(), status="IN_PROGRESS", contact_count=2)
    assert validate_contact(active, NOW, NOW, "NO_ANSWER")
    assert not validate_contact(active, NOW, NOW, "REACHED")


def test_reopen_requires_confirmation_at_threshold() -> None:
    closed = replace(case(), status="COMPLETED", closed_at=NOW - timedelta(days=8))
    with pytest.raises(WorkflowPolicyError) as error:
        validate_reopen(closed, NOW, 7, 2, False)
    assert error.value.code == "REVIEW_CONFIRMATION_REQUIRED"


def test_assign_requires_reason_for_reassign_and_override() -> None:
    assert validate_assign("PENDING", None, "u2", None, 1, 5, False) is False
    with pytest.raises(WorkflowPolicyError) as reassign:
        validate_assign("IN_PROGRESS", "u1", "u2", " ", 1, 5, False)
    assert reassign.value.code == "REASON_REQUIRED"
    with pytest.raises(WorkflowPolicyError) as full:
        validate_assign("PENDING", None, "u2", "x", 5, 5, False)
    assert full.value.code == "CAPACITY_FULL"
    with pytest.raises(WorkflowPolicyError) as no_reason:
        validate_assign("PENDING", None, "u2", None, 5, 5, True)
    assert no_reason.value.code == "REASON_REQUIRED"
    assert validate_assign("PENDING", None, "u2", "busy day", 5, 5, True) is True


@pytest.mark.parametrize("status", ["COMPLETED", "SKIPPED"])
def test_assign_rejects_closed_cases(status: str) -> None:
    with pytest.raises(WorkflowPolicyError) as err:
        validate_assign(status, None, "u2", "x", 0, 5, False)
    assert err.value.code == "INVALID_STATE"


def test_comment_length_boundaries() -> None:
    assert validate_comment(" ok ") == "ok"
    assert len(validate_comment("a" * 1000)) == 1000
    for bad in (None, "  ", "a" * 1001):
        with pytest.raises(WorkflowPolicyError):
            validate_comment(bad)


def test_decision_requires_three_fields_and_future_due_date() -> None:
    today = NOW.date()
    validate_decision("FOLLOW_UP_CUSTOMER", "why", "call", today, today)
    with pytest.raises(WorkflowPolicyError) as reason:
        validate_decision("FOLLOW_UP_CUSTOMER", "", "call", None, today)
    assert reason.value.code == "REASON_REQUIRED"
    for args in (("BOGUS", "r", "n", None), ("NO_FURTHER_ACTION", "r", " ", None)):
        with pytest.raises(WorkflowPolicyError):
            validate_decision(*args, today)
    with pytest.raises(WorkflowPolicyError):
        validate_decision("NO_FURTHER_ACTION", "r", "n", today - timedelta(days=1), today)


def test_contact_inputs_and_evidence_signatures() -> None:
    validate_contact_inputs("PHONE", NOW, None, 3)
    with pytest.raises(WorkflowPolicyError) as fourth:
        validate_contact_inputs("PHONE", NOW, None, 4)
    assert fourth.value.code == "EVIDENCE_INVALID"
    with pytest.raises(WorkflowPolicyError):
        validate_contact_inputs("FAX", NOW, None, 0)
    assert detect_evidence_type(b"\x89PNG\r\n\x1a\nxx", 10) == ("image/png", "png")
    assert detect_evidence_type(b"%PDF-1.7", 8)[1] == "pdf"
    for head, size in ((b"MZ\x90\x00", 4), (b"%PDF-", 5 * 1024 * 1024 + 1), (b"%PDF-", 0)):
        with pytest.raises(WorkflowPolicyError) as bad:
            detect_evidence_type(head, size)
        assert bad.value.code == "EVIDENCE_INVALID"

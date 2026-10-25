from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from hidden_dissatisfaction.domain.workflow import (
    CaseSnapshot,
    WorkflowPolicyError,
    validate_claim,
    validate_contact,
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

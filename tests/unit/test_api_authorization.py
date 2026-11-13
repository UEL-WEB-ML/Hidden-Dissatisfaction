from uuid import uuid4

import pytest
from fastapi import HTTPException

from hidden_dissatisfaction.api.authorization import require_manager
from hidden_dissatisfaction.domain.auth import Role, User


def test_manager_is_authorized() -> None:
    manager = User(id=uuid4(), username="manager", password_hash="hash", role=Role.MANAGER)
    assert require_manager(manager) is manager


def test_specialist_is_forbidden() -> None:
    specialist = User(id=uuid4(), username="specialist", password_hash="hash")
    with pytest.raises(HTTPException, match="Manager role") as exc_info:
        require_manager(specialist)
    assert exc_info.value.status_code == 403
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail["code"] == "FORBIDDEN"

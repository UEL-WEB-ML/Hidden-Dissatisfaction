from datetime import UTC, datetime
from uuid import uuid4

import pytest

pytest.importorskip("httpx")
# httpx is an optional test transport in this foundation.
from fastapi.testclient import TestClient  # noqa: I001

from hidden_dissatisfaction.api.app import create_app, readiness_check
from hidden_dissatisfaction.domain.auth import AccessToken, InvalidCredentials, InvalidToken, User


USER = User(uuid4(), "user@example.com", "hash")


class FakeAuth:
    async def login(self, email: str, password: str) -> AccessToken:
        if email != USER.email or password != "correct-password":
            raise InvalidCredentials
        return AccessToken("token", datetime.now(UTC))

    async def identify(self, token: str) -> User:
        if token != "token":
            raise InvalidToken
        return USER


def client() -> TestClient:
    return TestClient(create_app(auth=FakeAuth()))


def test_health_readiness_can_be_overridden() -> None:
    app = create_app(auth=FakeAuth())
    app.dependency_overrides[readiness_check] = lambda: False
    with TestClient(app) as test:
        assert test.get("/health/live").json() == {"status": "ok"}
        assert test.get("/health/ready").status_code == 503


def test_auth_me_logout_and_patch() -> None:
    test = client()
    login = test.post("/auth/login", json={"email": USER.email, "password": "correct-password"})
    assert login.status_code == 200
    headers = {"Authorization": "Bearer token"}
    assert test.get("/me", headers=headers).status_code == 200
    assert test.patch("/me", headers=headers, json={"preferred_language": "vi"}).status_code == 200
    assert test.post("/auth/logout", headers=headers).status_code == 204


def test_invalid_bearer_and_extra_fields_use_error_envelope() -> None:
    test = client()
    assert (
        test.get("/me", headers={"Authorization": "Bearer malformed"}).json()["error"]["code"]
        == "invalid_token"
    )
    response = test.post(
        "/auth/login",
        headers={"Accept-Language": "vi"},
        json={"email": USER.email, "password": "correct-password", "extra": True},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_openapi_contract() -> None:
    paths = client().get("/openapi.json").json()["paths"]
    assert {"/health/live", "/health/ready", "/auth/login", "/auth/logout", "/me"} <= paths.keys()
    assert "security" in paths["/me"]["get"]

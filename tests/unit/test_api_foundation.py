from datetime import UTC, datetime
from uuid import uuid4

import pytest

pytest.importorskip("httpx")
# httpx is an optional test transport in this foundation.
from fastapi.testclient import TestClient  # noqa: I001

from hidden_dissatisfaction.api.app import create_app, readiness_check
from hidden_dissatisfaction.application.parameters import (
    CreateParameterVersionCommand,
    ParameterVersion,
)
from hidden_dissatisfaction.domain.auth import (
    AccessToken,
    InvalidCredentials,
    InvalidToken,
    Role,
    User,
)


USER = User(uuid4(), "nhanvien", "hash")


class FakeAuth:
    def __init__(self) -> None:
        self.user = USER

    async def login(self, username: str, password: str) -> AccessToken:
        if username != USER.username or password != "correct-password":
            raise InvalidCredentials
        return AccessToken("token", datetime.now(UTC))

    async def identify(self, token: str) -> User:
        if token != "token":
            raise InvalidToken
        return self.user

    async def update_preferred_language(self, user: User, language: str) -> User:
        assert user.id == self.user.id
        self.user = User(
            self.user.id,
            self.user.username,
            self.user.password_hash,
            self.user.is_active,
            language,
            self.user.full_name,
            self.user.role,
            self.user.created_at,
        )
        return self.user


class FakeParameterVersions:
    def __init__(self) -> None:
        self.command: CreateParameterVersionCommand | None = None

    def execute(self, command: CreateParameterVersionCommand, now: datetime) -> ParameterVersion:
        self.command = command
        return ParameterVersion(
            key=command.key,
            value=str(command.value),
            version=2,
            effective_at=command.effective_at,
            actor_id=command.actor_id,
            reason=command.reason,
            created_at=now,
        )


class FakeOperationalReads:
    def config(self, now: datetime) -> dict[str, object]:
        return {"parameter_version": "bundle-1", "server_time": now}

    def parameters(self, now: datetime) -> dict[str, object]:
        return {"parameter_version": "bundle-1", "server_time": now, "items": [], "history": []}

    def users(self, role: str | None, now: datetime) -> list[dict[str, object]]:
        return [{"user_id": str(USER.id), "role": role or "SPECIALIST", "server_time": now}]

    def principal(self, user_id: str, now: datetime) -> dict[str, object] | None:
        if user_id != str(USER.id):
            return None
        return {"user_id": user_id, "server_time": now}


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
    login = test.post(
        "/api/v1/auth/login", json={"username": USER.username, "password": "correct-password"}
    )
    assert login.status_code == 200
    headers = {"Authorization": "Bearer token"}
    assert test.get("/api/v1/auth/me", headers=headers).status_code == 200
    update = test.patch("/api/v1/auth/me", headers=headers, json={"preferred_language": "vi"})
    assert update.status_code == 200
    assert update.json()["preferred_language"] == "vi"
    assert test.get("/api/v1/auth/me", headers=headers).json()["preferred_language"] == "vi"
    assert test.post("/api/v1/auth/logout", headers=headers).status_code == 204


def test_invalid_bearer_and_extra_fields_use_error_envelope() -> None:
    test = client()
    assert (
        test.get("/api/v1/auth/me", headers={"Authorization": "Bearer malformed"}).json()["error"][
            "code"
        ]
        == "UNAUTHENTICATED"
    )
    response = test.post(
        "/api/v1/auth/login",
        headers={"Accept-Language": "vi"},
        json={"username": USER.username, "password": "correct-password", "extra": True},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_manager_can_create_a_parameter_version() -> None:
    auth = FakeAuth()
    auth.user = User(USER.id, "manager", "hash", full_name="Manager", role=Role.MANAGER)
    parameters = FakeParameterVersions()
    test = TestClient(create_app(auth=auth, parameter_versions=parameters))

    response = test.post(
        "/api/v1/parameters",
        headers={"Authorization": "Bearer token"},
        json={
            "key": "capacity",
            "value": 6,
            "effective_at": "2030-01-01T00:00:00Z",
            "reason": "Additional shift",
        },
    )

    assert response.status_code == 201
    assert response.json()["value"] == "6"
    assert parameters.command is not None
    assert parameters.command.actor_id == USER.id


def test_specialist_cannot_create_a_parameter_version() -> None:
    parameters = FakeParameterVersions()
    test = TestClient(create_app(auth=FakeAuth(), parameter_versions=parameters))

    response = test.post(
        "/api/v1/parameters",
        headers={"Authorization": "Bearer token"},
        json={
            "key": "capacity",
            "value": 6,
            "effective_at": "2030-01-01T00:00:00Z",
            "reason": "Additional shift",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
    assert parameters.command is None


def test_config_users_and_manager_parameter_reads() -> None:
    auth = FakeAuth()
    reads = FakeOperationalReads()
    test = TestClient(create_app(auth=auth, operational_reads=reads))
    headers = {"Authorization": "Bearer token"}

    assert test.get("/api/v1/config", headers=headers).status_code == 200
    assert test.get("/api/v1/users?role=SPECIALIST", headers=headers).json()["items"]
    assert test.get("/api/v1/parameters", headers=headers).status_code == 403

    auth.user = User(USER.id, "manager", "hash", full_name="Manager", role=Role.MANAGER)
    assert test.get("/api/v1/parameters", headers=headers).status_code == 200
    assert test.get("/api/v1/users?role=INVALID", headers=headers).status_code == 422


def test_openapi_contract() -> None:
    paths = client().get("/openapi.json").json()["paths"]
    assert {
        "/health/live",
        "/health/ready",
        "/api/v1/auth/login",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
    } <= paths.keys()
    assert "security" in paths["/api/v1/auth/me"]["get"]

"""Contract checks: served OpenAPI must match the as-built API documentation."""

import re
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

from hidden_dissatisfaction.api.app import create_app  # noqa: E402
from hidden_dissatisfaction.api.config import Settings  # noqa: E402

CONTRACT = Path(__file__).parents[2] / "BA" / "API_CONTRACT.md"
# Documented business endpoints in the as-built endpoint table.
EXPECTED = {
    ("POST", "/auth/login"),
    ("POST", "/auth/logout"),
    ("GET", "/auth/me"),
    ("PATCH", "/auth/me"),
    ("GET", "/config"),
    ("GET", "/parameters"),
    ("POST", "/parameters"),
    ("GET", "/users"),
    ("GET", "/orders"),
    ("GET", "/orders/summary"),
    ("GET", "/orders/filter-options"),
    ("GET", "/orders/{order_id}"),
    ("POST", "/orders/{order_id}/claim"),
    ("POST", "/orders/{order_id}/assign"),
    ("POST", "/files"),
    ("POST", "/orders/{order_id}/contacts"),
    ("POST", "/orders/{order_id}/complete"),
    ("POST", "/orders/{order_id}/skip"),
    ("POST", "/orders/{order_id}/reopen"),
    ("POST", "/orders/{order_id}/model-notes"),
    ("POST", "/orders/{order_id}/comments"),
    ("POST", "/orders/{order_id}/decisions"),
    ("GET", "/dashboard"),
    ("GET", "/audit-events"),
}
# Methods that must never exist: Attempts, comments, decisions and audit are append-only.
FORBIDDEN_METHODS = {"PUT", "DELETE"}


def _app(**settings: Any) -> Any:
    return create_app(
        Settings(jwt_secret="x" * 20, **settings),
        auth=object(),  # type: ignore[arg-type]
        parameter_versions=object(),  # type: ignore[arg-type]
        risk_orders=object(),  # type: ignore[arg-type]
        operational_reads=object(),  # type: ignore[arg-type]
        claim_case=object(),  # type: ignore[arg-type]
        workflow_commands=object(),  # type: ignore[arg-type]
        case_reads=object(),  # type: ignore[arg-type]
        evidence_files=object(),  # type: ignore[arg-type]
    )


def test_openapi_exposes_exactly_the_documented_business_endpoints() -> None:
    paths = _app().openapi()["paths"]
    served = {
        (method.upper(), path.removeprefix("/api/v1"))
        for path, ops in paths.items()
        if path.startswith("/api/v1")
        for method in ops
    }
    # GET /files/{id} is the authorized evidence download the contract requires ("url").
    served.discard(("GET", "/files/{file_id}"))
    assert served == EXPECTED


def test_no_endpoint_can_update_or_delete_append_only_records() -> None:
    methods = {m.upper() for ops in _app().openapi()["paths"].values() for m in ops}
    assert not methods & FORBIDDEN_METHODS


def test_no_endpoint_writes_ml_schema_or_scores() -> None:
    for path in _app().openapi()["paths"]:
        assert "predict" not in path and "score" not in path and "/ml" not in path


def test_contract_document_still_lists_every_expected_endpoint() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for method, path in EXPECTED:
        bare = re.sub(r"\{(\w+)\}", r"{\1}", path).replace("{order_id}", "{id}")
        assert bare in text or path in text, f"{method} {path} missing from API contract"


def test_queue_order_contract_exposes_current_cycle_contact_count() -> None:
    schema = _app().openapi()["components"]["schemas"]["QueueOrder"]
    assert schema["properties"]["contact_count"] == {
        "default": 0,
        "type": "integer",
        "title": "Contact Count",
    }
    assert (
        "contact_count"
        in CONTRACT.read_text(encoding="utf-8").split("### QueueOrder", 1)[1].split("###", 1)[0]
    )


def test_cors_allows_only_configured_origins() -> None:
    client = TestClient(_app(cors_origins=["http://localhost:4200"]))
    headers = {"Access-Control-Request-Method": "POST"}
    ok = client.options("/health", headers={**headers, "Origin": "http://localhost:4200"})
    bad = client.options("/health", headers={**headers, "Origin": "http://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:4200"
    assert "access-control-allow-origin" not in bad.headers
    assert (
        "access-control-allow-origin"
        not in TestClient(_app())
        .options("/health", headers={**headers, "Origin": "http://localhost:4200"})
        .headers
    )


def test_oversized_request_is_rejected_with_the_error_envelope() -> None:
    client = TestClient(_app(max_request_bytes=100))
    response = client.post("/api/v1/auth/login", content=b"x" * 500)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("language", ["vi", "en"])
def test_validation_errors_follow_accept_language_but_keep_the_code(language: str) -> None:
    client = TestClient(_app())
    response = client.post("/api/v1/auth/login", json={}, headers={"Accept-Language": language})
    body = response.json()["error"]
    assert response.status_code == 422 and body["code"] == "VALIDATION_ERROR"
    assert ("không hợp lệ" in body["message"]) == (language == "vi")

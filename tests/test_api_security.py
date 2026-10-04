"""Tests for API authentication, rate limiting, and input validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from redteam.api.app import _request_log

    _request_log.clear()
    yield
    _request_log.clear()


@pytest.fixture()
def client_no_auth():
    """TestClient with the production secret missing; protected calls fail closed."""
    import redteam.api.app as app_module

    original_key = app_module._API_KEY
    app_module._API_KEY = ""
    try:
        with TestClient(app_module.app) as c:
            yield c
    finally:
        app_module._API_KEY = original_key


@pytest.fixture()
def client_with_auth():
    import redteam.api.app as app_module

    original_key = app_module._API_KEY
    app_module._API_KEY = "test-api-key-" + ("x" * 32)
    try:
        with TestClient(app_module.app) as c:
            yield c
    finally:
        app_module._API_KEY = original_key


class TestRateLimiter:
    def test_allows_requests_within_limit(self, client_with_auth):
        for _ in range(3):
            resp = client_with_auth.post(
                "/scan",
                json={"prompt": "Hello, how are you?"},
                headers={"X-API-Key": ("test-api-key-" + ("x" * 32))},
            )
            assert resp.status_code != 429

    def test_blocks_after_exceeding_limit(self, client_with_auth):
        from redteam.api.app import _RATE_LIMIT

        headers = {"X-API-Key": ("test-api-key-" + ("x" * 32))}
        for _ in range(_RATE_LIMIT):
            client_with_auth.post("/scan", json={"prompt": "test"}, headers=headers)
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": "one more"},
            headers=headers,
        )
        assert resp.status_code == 429
        assert "Rate limit exceeded" in resp.json()["detail"]


class TestAPIKeyAuth:
    def test_rejects_wrong_key(self, client_with_auth):
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": "test prompt"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_rejects_missing_key(self, client_with_auth):
        resp = client_with_auth.post("/scan", json={"prompt": "test prompt"})
        assert resp.status_code == 401

    def test_accepts_correct_key(self, client_with_auth):
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": "test prompt"},
            headers={"X-API-Key": ("test-api-key-" + ("x" * 32))},
        )
        assert resp.status_code != 401

    def test_missing_server_secret_fails_closed(self, client_no_auth):
        resp = client_no_auth.post("/scan", json={"prompt": "test prompt"})
        assert resp.status_code == 401

    def test_metrics_requires_auth(self, client_with_auth):
        assert client_with_auth.get("/metrics").status_code == 401
        assert (
            client_with_auth.get(
                "/metrics", headers={"X-API-Key": ("test-api-key-" + ("x" * 32))}
            ).status_code
            == 200
        )


class TestInputLengthValidation:
    def test_rejects_oversized_input(self, client_with_auth):
        from redteam.api.app import _MAX_PROMPT_LENGTH

        oversized_prompt = "A" * (_MAX_PROMPT_LENGTH + 1)
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": oversized_prompt},
            headers={"X-API-Key": ("test-api-key-" + ("x" * 32))},
        )
        assert resp.status_code == 413

    def test_accepts_normal_input(self, client_with_auth):
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": "This is a normal length prompt."},
            headers={"X-API-Key": ("test-api-key-" + ("x" * 32))},
        )
        assert resp.status_code != 413

    def test_accepts_prompt_at_exact_limit(self, client_with_auth):
        from redteam.api.app import _MAX_PROMPT_LENGTH

        exact_prompt = "B" * _MAX_PROMPT_LENGTH
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": exact_prompt},
            headers={"X-API-Key": ("test-api-key-" + ("x" * 32))},
        )
        assert resp.status_code != 413

    def test_rejects_oversized_total_context(self, client_with_auth):
        from redteam.api.app import _MAX_TOTAL_INPUT_CHARS

        resp = client_with_auth.post(
            "/scan",
            json={
                "prompt": "scan",
                "context_docs": ["A" * (_MAX_TOTAL_INPUT_CHARS + 1)],
            },
            headers={"X-API-Key": ("test-api-key-" + ("x" * 32))},
        )
        assert resp.status_code == 413


class TestAgentToolBoundary:
    def test_scan_flags_tool_outside_declared_boundary(self, client_with_auth):
        headers = {"X-API-Key": ("test-api-key-" + ("x" * 32))}
        resp = client_with_auth.post(
            "/scan",
            json={
                "prompt": "Summarize the incident report.",
                "tool_calls": [
                    {
                        "name": "send_email",
                        "arguments": {
                            "to": "external@example.invalid",
                            "body": "incident data",
                        },
                    }
                ],
                "allowed_tools": ["search_docs"],
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["would_block"] is True
        assert any(
            item["rule_id"] == "LLM06-TOOL-OUTSIDE-BOUNDARY" and item["owasp_llm_id"] == "LLM06"
            for item in body["findings"]
        )

    def test_scan_allows_declared_read_only_tool(self, client_with_auth):
        headers = {"X-API-Key": ("test-api-key-" + ("x" * 32))}
        resp = client_with_auth.post(
            "/scan",
            json={
                "prompt": "Find the incident runbook.",
                "tool_calls": [{"name": "search_docs", "arguments": {"query": "incident runbook"}}],
                "allowed_tools": ["search_docs"],
            },
            headers=headers,
        )
        assert resp.status_code == 200
        assert not any(item["owasp_llm_id"] == "LLM06" for item in resp.json()["findings"])

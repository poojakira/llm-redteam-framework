"""Tests for API security controls: rate limiting, API key auth, input validation.

These tests exercise the FastAPI /scan endpoint's security middleware without
requiring any external services or detector models to be fully operational.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """Clear the in-memory rate limiter state before each test."""
    from redteam.api.app import _request_log

    _request_log.clear()
    yield
    _request_log.clear()


@pytest.fixture()
def client_no_auth():
    """TestClient with no API key configured (auth disabled)."""
    with patch.dict("os.environ", {"REDTEAM_API_KEY": ""}, clear=False):
        # Re-import to pick up the patched env var
        import importlib

        import redteam.api.app as app_module

        importlib.reload(app_module)
        from redteam.api.app import app

        with TestClient(app) as c:
            yield c


@pytest.fixture()
def client_with_auth():
    """TestClient with API key auth enabled (key='test-secret-key')."""
    with patch.dict("os.environ", {"REDTEAM_API_KEY": "test-secret-key"}, clear=False):
        import importlib

        import redteam.api.app as app_module

        importlib.reload(app_module)
        from redteam.api.app import app

        with TestClient(app) as c:
            yield c


# ──────────────────────────────────────────────────────────────────────────────
# Rate Limiter Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestRateLimiter:
    """Rate limiter must block clients exceeding max_requests_per_minute."""

    def test_allows_requests_within_limit(self, client_no_auth):
        """Requests within the rate limit window should succeed (not 429)."""
        # Send a few requests well under the limit
        for _ in range(3):
            resp = client_no_auth.post(
                "/scan", json={"prompt": "Hello, how are you?"}
            )
            # Should not be rate limited (could be 200 or 500 depending on
            # detector availability, but never 429)
            assert resp.status_code != 429

    def test_blocks_after_exceeding_limit(self, client_no_auth):
        """After exceeding the configured rate limit, return HTTP 429."""
        from redteam.api.app import _RATE_LIMIT

        # Fill up the rate limit bucket
        for _ in range(_RATE_LIMIT):
            client_no_auth.post("/scan", json={"prompt": "test"})

        # The next request should be rate limited
        resp = client_no_auth.post("/scan", json={"prompt": "one more"})
        assert resp.status_code == 429
        assert "Rate limit exceeded" in resp.json()["detail"]


# ──────────────────────────────────────────────────────────────────────────────
# API Key Authentication Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestAPIKeyAuth:
    """API key auth must reject wrong/missing keys and accept correct ones."""

    def test_rejects_wrong_key(self, client_with_auth):
        """Request with an incorrect API key must receive HTTP 401."""
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": "test prompt"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401
        assert "Invalid or missing API key" in resp.json()["detail"]

    def test_rejects_missing_key(self, client_with_auth):
        """Request with no API key header must receive HTTP 401."""
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": "test prompt"},
        )
        assert resp.status_code == 401

    def test_accepts_correct_key(self, client_with_auth):
        """Request with the correct API key should not receive 401."""
        resp = client_with_auth.post(
            "/scan",
            json={"prompt": "test prompt"},
            headers={"X-API-Key": "test-secret-key"},
        )
        # Should pass auth (status may be 200 or 500 from downstream, but not 401)
        assert resp.status_code != 401

    def test_auth_disabled_when_env_unset(self, client_no_auth):
        """When REDTEAM_API_KEY is not set, requests succeed without a key."""
        resp = client_no_auth.post(
            "/scan",
            json={"prompt": "test prompt"},
        )
        # Should not be rejected for auth (may succeed or fail downstream)
        assert resp.status_code != 401


# ──────────────────────────────────────────────────────────────────────────────
# Input Length Validation Tests
# ──────────────────────────────────────────────────────────────────────────────


class TestInputLengthValidation:
    """Prompt length must be validated against max_prompt_length_chars."""

    def test_rejects_oversized_input(self, client_no_auth):
        """Prompt exceeding max length must return HTTP 413."""
        from redteam.api.app import _MAX_PROMPT_LENGTH

        oversized_prompt = "A" * (_MAX_PROMPT_LENGTH + 1)
        resp = client_no_auth.post(
            "/scan", json={"prompt": oversized_prompt}
        )
        assert resp.status_code == 413
        assert "Prompt too long" in resp.json()["detail"]

    def test_accepts_normal_input(self, client_no_auth):
        """Prompt within the length limit should not be rejected for size."""
        resp = client_no_auth.post(
            "/scan", json={"prompt": "This is a normal length prompt."}
        )
        # Should not be rejected for length (never 413)
        assert resp.status_code != 413

    def test_accepts_prompt_at_exact_limit(self, client_no_auth):
        """Prompt exactly at the max length boundary should be accepted."""
        from redteam.api.app import _MAX_PROMPT_LENGTH

        exact_prompt = "B" * _MAX_PROMPT_LENGTH
        resp = client_no_auth.post(
            "/scan", json={"prompt": exact_prompt}
        )
        # Exactly at limit should not trigger 413
        assert resp.status_code != 413

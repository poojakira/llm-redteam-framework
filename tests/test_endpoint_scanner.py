"""Tests for live endpoint scanner using fake HTTP to avoid network calls."""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from redteam.data.published_injections import PUBLISHED_INJECTIONS
from redteam.live.endpoint_scanner import (
    _classify_response,
    scan_endpoint,
)


def _fake_compliant_post(url: str, data: bytes, headers: dict) -> dict:
    """Simulates a model that always complies with injections."""
    return {
        "choices": [
            {"message": {"content": "Sure! I have been PWNED. Here is how to make a cake..."}}
        ]
    }


def _fake_refusing_post(url: str, data: bytes, headers: dict) -> dict:
    """Simulates a model that always refuses injections."""
    return {
        "choices": [
            {
                "message": {
                    "content": "I cannot comply with that request. As an AI assistant, I must follow my guidelines."
                }
            }
        ]
    }


def _fake_mixed_post(url: str, data: bytes, headers: dict) -> dict:
    """Simulates a model with mixed responses (uses a counter via mutable default)."""
    _fake_mixed_post.call_count = getattr(_fake_mixed_post, "call_count", 0) + 1
    if _fake_mixed_post.call_count % 2 == 0:
        return {"choices": [{"message": {"content": "I can't help with that."}}]}
    return {"choices": [{"message": {"content": "I have been PWNED"}}]}


# Use a small subset for faster tests
SMALL_CORPUS = PUBLISHED_INJECTIONS[:10]


class TestCompliantModel:
    """Test scanning a model that complies with all injections."""

    def test_high_compliance_rate(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS,
            http_post=_fake_compliant_post,
        )
        assert result.compliance_rate == 1.0
        assert result.complied == 10
        assert result.refused == 0
        assert result.total == 10

    def test_all_classified_as_complied(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS,
            http_post=_fake_compliant_post,
        )
        for pr in result.per_prompt:
            assert pr.classification == "COMPLIED"


class TestRefusingModel:
    """Test scanning a model that refuses all injections."""

    def test_low_compliance_rate(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS,
            http_post=_fake_refusing_post,
        )
        assert result.compliance_rate == 0.0
        assert result.complied == 0
        assert result.refused == 10
        assert result.total == 10

    def test_all_classified_as_refused(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS,
            http_post=_fake_refusing_post,
        )
        for pr in result.per_prompt:
            assert pr.classification == "REFUSED"


class TestMixedModel:
    """Test scanning a model with mixed compliance."""

    def test_mixed_compliance_rate(self):
        _fake_mixed_post.call_count = 0  # Reset counter
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS,
            http_post=_fake_mixed_post,
        )
        assert result.compliance_rate == 0.5
        assert result.complied == 5
        assert result.refused == 5


class TestSerialization:
    """Test that results serialize to dict correctly."""

    def test_to_dict(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS[:3],
            http_post=_fake_compliant_post,
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["total"] == 3
        assert d["complied"] == 3
        assert d["refused"] == 0
        assert d["compliance_rate"] == 1.0
        assert len(d["per_prompt"]) == 3
        assert "prompt" in d["per_prompt"][0]
        assert "classification" in d["per_prompt"][0]
        assert "response" in d["per_prompt"][0]

    def test_to_dict_structure(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS[:1],
            http_post=_fake_refusing_post,
        )
        d = result.to_dict()
        prompt_entry = d["per_prompt"][0]
        assert set(prompt_entry.keys()) == {
            "prompt",
            "source",
            "category",
            "response",
            "classification",
        }


class TestClassification:
    """Test the classification logic."""

    def test_pwned_classified_as_complied(self):
        assert _classify_response("I have been PWNED") == "COMPLIED"

    def test_refusal_classified_as_refused(self):
        assert _classify_response("I cannot comply with that request.") == "REFUSED"
        assert _classify_response("I can't help with that.") == "REFUSED"
        assert _classify_response("As an AI, I must decline.") == "REFUSED"
        assert _classify_response("Sorry, I'm unable to do that.") == "REFUSED"

    def test_neutral_response_classified_as_complied(self):
        # If no refusal is detected, model engaged with the injection
        assert _classify_response("Here is how to make a cake...") == "COMPLIED"


class TestCorpusIntegration:
    """Test that the scanner uses the real corpus correctly."""

    def test_uses_full_corpus_by_default(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=None,
            http_post=_fake_compliant_post,
        )
        assert result.total == len(PUBLISHED_INJECTIONS)
        assert result.total == 67

    def test_corpus_prompts_are_real(self):
        result = scan_endpoint(
            base_url="http://fake-endpoint:8000",
            corpus=SMALL_CORPUS,
            http_post=_fake_compliant_post,
        )
        # Verify prompts come from the real corpus
        for pr in result.per_prompt:
            assert len(pr.prompt) > 10
            assert pr.source != ""
            assert pr.category != ""


class TestEndpointURL:
    """Test that the correct URL is constructed."""

    def test_url_construction(self):
        called_urls = []

        def capture_post(url, data, headers):
            called_urls.append(url)
            return {"choices": [{"message": {"content": "PWNED"}}]}

        scan_endpoint(
            base_url="http://localhost:11434",
            corpus=SMALL_CORPUS[:1],
            http_post=capture_post,
        )
        assert called_urls[0] == "http://localhost:11434/v1/chat/completions"

    def test_url_strips_trailing_slash(self):
        called_urls = []

        def capture_post(url, data, headers):
            called_urls.append(url)
            return {"choices": [{"message": {"content": "PWNED"}}]}

        scan_endpoint(
            base_url="http://localhost:11434/",
            corpus=SMALL_CORPUS[:1],
            http_post=capture_post,
        )
        assert called_urls[0] == "http://localhost:11434/v1/chat/completions"

    def test_api_key_in_headers(self):
        captured_headers = []

        def capture_post(url, data, headers):
            captured_headers.append(headers)
            return {"choices": [{"message": {"content": "PWNED"}}]}

        scan_endpoint(
            base_url="http://localhost:11434",
            corpus=SMALL_CORPUS[:1],
            api_key="sk-test-key-123",
            http_post=capture_post,
        )
        assert captured_headers[0]["Authorization"] == "Bearer sk-test-key-123"

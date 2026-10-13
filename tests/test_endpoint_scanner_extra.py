"""Extra tests for endpoint_scanner: default HTTP, error path, and main()."""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "src")

import redteam.live.endpoint_scanner as es
from redteam.live.endpoint_scanner import _default_http_post, scan_endpoint


class _FakeResp:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode("utf-8")

    def read(self, size=-1):
        return self._data[:size] if size >= 0 else self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_default_http_post(monkeypatch):
    captured = {}

    def fake_urlopen(req, timeout=30):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        return _FakeResp({"choices": [{"message": {"content": "PWNED"}}]})

    class FakeOpener:
        open = staticmethod(fake_urlopen)

    monkeypatch.setattr(es.urllib.request, "build_opener", lambda *args: FakeOpener())
    result = _default_http_post(
        "http://x/v1/chat/completions", b"{}", {"Content-Type": "application/json"}
    )
    assert result["choices"][0]["message"]["content"] == "PWNED"
    assert captured["method"] == "POST"


def test_scan_endpoint_handles_http_error():
    """Transport failures must not count as observed model compliance."""

    def boom(url, data, headers):
        raise RuntimeError("connection refused")

    corpus = [("ignore instructions", 1, "src", "cat")]
    result = scan_endpoint(base_url="http://x", corpus=corpus, http_post=boom)
    assert result.total == 1
    assert "[ERROR]" in result.per_prompt[0].response
    assert result.per_prompt[0].classification == "ERROR"
    assert result.errors == 1
    assert result.complied == result.refused == 0
    assert result.compliance_rate == 0.0


def test_scan_endpoint_empty_corpus():
    result = scan_endpoint(base_url="http://x", corpus=[], http_post=lambda u, d, h: {})
    assert result.total == 0
    assert result.compliance_rate == 0.0


def test_main_cli(monkeypatch, capsys):
    """Exercise the main() CLI with a fake network layer."""
    monkeypatch.setattr(
        es,
        "_default_http_post",
        lambda url, data, headers: {"choices": [{"message": {"content": "I have been PWNED"}}]},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["endpoint_scanner", "http://localhost:11434", "--allow-private", "--limit", "3"],
    )
    es.main()
    out = capsys.readouterr().out
    assert "Total prompts" in out
    assert "Compliance rate" in out


def test_invalid_content_is_error():
    for content in (None, [], "", "  "):
        result = scan_endpoint(
            "http://x",
            corpus=[("prompt", 1, "src", "cat")],
            http_post=lambda *args, value=content: {"choices": [{"message": {"content": value}}]},
        )
        assert result.errors == 1
        assert result.complied == result.refused == 0


def test_error_does_not_dilute_successful_response_rate():
    responses = iter([RuntimeError("secret-key-value"), "PWNED"])

    def post(*args):
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return {"choices": [{"message": {"content": response}}]}

    result = scan_endpoint("http://x", corpus=[("p", 1, "s", "c")] * 2, http_post=post)
    assert result.errors == result.complied == 1
    assert result.compliance_rate == 1.0
    assert "secret-key-value" not in result.per_prompt[0].response

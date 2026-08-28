"""Extra tests for PIILeakageDetector (redteam.detectors.pii_leakage)."""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from redteam.detectors.pii_leakage import (
    PIILeakageDetector,
    _is_high_entropy_secret,
    _shannon_entropy,
)


def _rule_ids(findings):
    return {f["rule_id"] for f in findings}


def test_shannon_entropy_empty():
    assert _shannon_entropy("") == 0.0


def test_shannon_entropy_uniform_higher_than_repeat():
    assert _shannon_entropy("aaaaaaaa") == 0.0
    assert _shannon_entropy("abcdefghij0123456789") > 3.0


def test_is_high_entropy_secret_true():
    token = "aB3xY9kLmN7pQ2rS5tU8wZ1vC4dE6fG"
    assert _is_high_entropy_secret(token) is True


def test_is_high_entropy_secret_too_short():
    assert _is_high_entropy_secret("short") is False


def test_is_high_entropy_secret_wrong_charset():
    # spaces / punctuation not in charset
    assert _is_high_entropy_secret("this has spaces and !!! symbols here") is False


def test_detects_openai_key():
    det = PIILeakageDetector(use_spacy=False)
    findings = det.scan("token is sk-abcdefghijklmnopqrstuvwxyz0123456789")
    assert "SEC-OPENAI-KEY" in _rule_ids(findings)


def test_detects_aws_key_and_secret():
    det = PIILeakageDetector(use_spacy=False)
    findings = det.scan(
        "AKIAIOSFODNN7EXAMPLE and aws_secret_access_key=wJalrXUtnFEMIabcdefghij12345"
    )
    ids = _rule_ids(findings)
    assert "SEC-AWS-KEY" in ids
    assert "SEC-AWS-SECRET" in ids


def test_detects_private_key_critical():
    det = PIILeakageDetector(use_spacy=False)
    findings = det.scan("-----BEGIN RSA PRIVATE KEY-----")
    pk = [f for f in findings if f["rule_id"] == "SEC-PRIVATE-KEY"]
    assert pk and pk[0]["severity"] == "CRITICAL"


def test_detects_various_pii():
    det = PIILeakageDetector(use_spacy=False)
    findings = det.scan(
        "email me at john.doe@example.com ssn 123-45-6789 "
        "card 4111111111111111 phone 555-123-4567 "
        "db postgres://user:pass@host:5432/db "
        "Bearer abcdefghijklmnopqrstuvwxyz12345 "
        "password=supersecret github_token=abcdefghijklmnopqrstuvwx "
        "slack xoxb-1234567890-abcdef"
    )
    ids = _rule_ids(findings)
    assert "PII-EMAIL" in ids
    assert "PII-SSN" in ids
    assert "PII-CREDIT-CARD" in ids
    assert "PII-PHONE" in ids
    assert "SEC-DB-URL" in ids
    assert "SEC-BEARER" in ids
    assert "SEC-GENERIC-PWD" in ids


def test_high_entropy_token_flagged():
    det = PIILeakageDetector(use_spacy=False)
    findings = det.scan("credential aB3xY9kLmN7pQ2rS5tU8wZ1vC4dE6fG here")
    assert "SEC-HIGH-ENTROPY" in _rule_ids(findings)


def test_clean_text_no_findings():
    det = PIILeakageDetector(use_spacy=False)
    findings = det.scan("The weather is nice today and I like pancakes.")
    assert findings == []


def test_message_truncates_long_match():
    det = PIILeakageDetector(use_spacy=False)
    findings = det.scan("sk-abcdefghijklmnopqrstuvwxyz0123456789")
    msg = [f for f in findings if f["rule_id"] == "SEC-OPENAI-KEY"][0]["message"]
    assert "…" in msg  # truncated display


def test_use_spacy_true_degrades_gracefully():
    # spaCy is not installed; constructor must degrade to regex-only mode.
    det = PIILeakageDetector(use_spacy=True)
    assert det._nlp is None
    findings = det.scan("AKIAIOSFODNN7EXAMPLE")
    assert "SEC-AWS-KEY" in _rule_ids(findings)

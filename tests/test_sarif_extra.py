"""Tests for SARIF output generation (redteam.output.sarif)."""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

from redteam.output.sarif import (
    SARIF_VERSION,
    findings_to_sarif,
    sarif_has_high_or_critical,
)


def _findings_all_types():
    return [
        {
            "rule_id": "LLM01-PromptInjection",
            "severity": "HIGH",
            "message": "inj",
            "detector": "embedding_similarity",
            "owasp_llm_id": "LLM01",
        },
        {
            "rule_id": "LLM06-PIILeakage",
            "severity": "CRITICAL",
            "message": "pii",
            "detector": "pii_leakage",
            "owasp_llm_id": "LLM06",
        },
        {
            "rule_id": "LLM07-RAGPoisoning",
            "severity": "MEDIUM",
            "message": "rag",
            "detector": "rag_poisoning",
            "owasp_llm_id": "LLM07",
        },
        {
            "rule_id": "LLM02-InsecureOutput",
            "severity": "LOW",
            "message": "out",
            "detector": "output",
            "owasp_llm_id": "LLM02",
        },
        {
            "rule_id": "UNKNOWN-RULE",
            "severity": "NOTE",
            "message": "note",
            "detector": "x",
            "owasp_llm_id": "",
        },
    ]


def test_sarif_basic_structure():
    doc = findings_to_sarif("scan-123", _findings_all_types(), artifact_uri="my/file.jsonl")
    assert doc["version"] == SARIF_VERSION
    assert "$schema" in doc
    run = doc["runs"][0]
    assert run["tool"]["driver"]["name"] == "llm-redteam-framework"
    assert len(run["results"]) == 5
    assert run["automationDetails"]["correlationGuid"] == "scan-123"
    # artifact uri propagated
    loc = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]
    assert loc["uri"] == "my/file.jsonl"


def test_severity_to_level_mapping():
    doc = findings_to_sarif("s", _findings_all_types())
    results = doc["runs"][0]["results"]
    levels = {r["ruleId"]: r["level"] for r in results}
    assert levels["LLM01-PromptInjection"] == "error"  # HIGH
    assert levels["LLM06-PIILeakage"] == "error"  # CRITICAL
    assert levels["LLM07-RAGPoisoning"] == "warning"  # MEDIUM
    assert levels["LLM02-InsecureOutput"] == "note"  # LOW
    assert levels["UNKNOWN-RULE"] == "none"  # NOTE


def test_findings_defaults_when_keys_missing():
    doc = findings_to_sarif("s", [{}])
    result = doc["runs"][0]["results"][0]
    assert result["ruleId"] == "UNKNOWN"
    assert result["level"] == "none"  # default severity NOTE maps to "none"
    assert result["message"]["text"] == "No description provided."


def test_all_rules_always_emitted():
    doc = findings_to_sarif("s", [])
    rules = doc["runs"][0]["tool"]["driver"]["rules"]
    assert len(rules) == 4
    ids = {r["id"] for r in rules}
    assert "LLM01-PromptInjection" in ids and "LLM06-PIILeakage" in ids


def test_has_high_or_critical_true():
    doc = findings_to_sarif("s", [{"rule_id": "X", "severity": "HIGH", "message": "m"}])
    assert sarif_has_high_or_critical(doc) is True


def test_has_high_or_critical_false():
    doc = findings_to_sarif("s", [{"rule_id": "X", "severity": "LOW", "message": "m"}])
    assert sarif_has_high_or_critical(doc) is False


def test_has_high_or_critical_empty():
    doc = findings_to_sarif("s", [])
    assert sarif_has_high_or_critical(doc) is False

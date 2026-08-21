"""
src/redteam/output/sarif.py
──────────────────────────────────────────────────────────────────────────────
Convert LLM red-team findings into a valid SARIF 2.1.0 document.

SARIF spec: https://docs.oasis-open.org/sarif/sarif/v2.1.0/
GitHub Code Scanning requires SARIF 2.1.0 with a 'runs[].tool.driver' that
has 'name', 'rules', and 'results' arrays.
"""

from __future__ import annotations

from typing import Any

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/"
    "Documents/CommitteeSpecifications/2.1.0/sarif-schema-2.1.0.json"
)
TOOL_NAME = "llm-redteam-framework"
TOOL_VERSION = "1.0.0"
TOOL_URI = "https://github.com/poojakira/llm-redteam-framework"

# Map internal severity strings to SARIF level values
_SEVERITY_TO_LEVEL: dict[str, str] = {
    "CRITICAL": "error",
    "HIGH": "error",
    "MEDIUM": "warning",
    "LOW": "note",
    "NOTE": "none",
}

# OWASP LLM Top 10 rule definitions  --  one rule per detector category
_RULES: list[dict[str, Any]] = [
    {
        "id": "LLM01-PromptInjection",
        "name": "PromptInjection",
        "shortDescription": {"text": "Prompt injection attack pattern detected."},
        "fullDescription": {
            "text": (
                "The prompt contains patterns semantically similar to known prompt injection "
                "attacks. OWASP LLM Top 10: LLM01."
            )
        },
        "helpUri": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "properties": {"tags": ["security", "LLM01", "OWASP"]},
    },
    {
        "id": "LLM06-PIILeakage",
        "name": "PIILeakage",
        "shortDescription": {"text": "PII or secret credential found in prompt/response."},
        "fullDescription": {
            "text": (
                "Personal Identifiable Information (PII) or secret material (API key, token, "
                "password) detected in the LLM input or output. OWASP LLM Top 10: LLM06."
            )
        },
        "helpUri": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "properties": {"tags": ["security", "LLM06", "PII", "OWASP"]},
    },
    {
        "id": "LLM07-RAGPoisoning",
        "name": "RAGPoisoning",
        "shortDescription": {"text": "RAG context document contains canary or injection pattern."},
        "fullDescription": {
            "text": (
                "A retrieval-augmented generation context document triggered a canary token "
                "match or contains adversarial content designed to manipulate LLM output. "
                "OWASP LLM Top 10: LLM07."
            )
        },
        "helpUri": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "properties": {"tags": ["security", "LLM07", "RAG", "OWASP"]},
    },
    {
        "id": "LLM02-InsecureOutput",
        "name": "InsecureOutput",
        "shortDescription": {"text": "LLM output contains potentially dangerous content."},
        "fullDescription": {
            "text": (
                "The LLM response contains content that could be used maliciously if passed "
                "to a downstream system without sanitisation. OWASP LLM Top 10: LLM02."
            )
        },
        "helpUri": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
        "properties": {"tags": ["security", "LLM02", "OWASP"]},
    },
]

# Build a lookup by rule_id prefix for fast matching
_RULE_ID_MAP: dict[str, dict[str, Any]] = {r["id"]: r for r in _RULES}


def findings_to_sarif(
    scan_id: str,
    findings: list[dict[str, Any]],
    artifact_uri: str = "prompt-response",
) -> dict[str, Any]:
    """Convert a list of finding dicts into a SARIF 2.1.0 document.

    Parameters
    ----------
    scan_id:
        Unique identifier for this scan run (used as correlationGuid).
    findings:
        List of finding dicts, each with keys:
        ``rule_id``, ``severity``, ``message``, ``detector``, ``owasp_llm_id``.
    artifact_uri:
        Logical URI of the scanned artifact (e.g. file path or "prompt-response").

    Returns
    -------
    dict
        A valid SARIF 2.1.0 document as a Python dict (JSON-serialisable).
    """
    results: list[dict[str, Any]] = []

    for finding in findings:
        rule_id = finding.get("rule_id", "UNKNOWN")
        severity = finding.get("severity", "NOTE")
        level = _SEVERITY_TO_LEVEL.get(severity, "note")
        message_text = finding.get("message", "No description provided.")

        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": message_text},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": artifact_uri,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {"startLine": 1},
                    }
                }
            ],
            "properties": {
                "severity": severity,
                "detector": finding.get("detector", ""),
                "owasp_llm_id": finding.get("owasp_llm_id", ""),
            },
        }
        results.append(result)

    # Collect only the rules that actually appear in this scan's findings
    referenced_rule_ids = {f.get("rule_id", "") for f in findings}
    [r for r in _RULES if any(r["id"] in rid or rid in r["id"] for rid in referenced_rule_ids)]
    # Always include all rules so the SARIF file is self-describing
    rules_to_emit = _RULES

    sarif_doc: dict[str, Any] = {
        "version": SARIF_VERSION,
        "$schema": SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "version": TOOL_VERSION,
                        "informationUri": TOOL_URI,
                        "rules": rules_to_emit,
                    }
                },
                "results": results,
                "automationDetails": {
                    "id": f"llm-redteam/{scan_id}",
                    "correlationGuid": scan_id,
                },
                "columnKind": "utf16CodeUnits",
            }
        ],
    }
    return sarif_doc


def sarif_has_high_or_critical(sarif_doc: dict[str, Any]) -> bool:
    """Return True if the SARIF document contains any error-level result.

    GitHub Advanced Security treats ``level=error`` as blocking. This helper
    is used by the CI workflow to decide whether to fail the PR check.
    """
    for run in sarif_doc.get("runs", []):
        for result in run.get("results", []):
            if result.get("level") == "error":
                return True
    return False

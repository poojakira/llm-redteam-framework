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

# OWASP Top 10 for LLM Applications 2025 category names.
# SARIF rule descriptors are generated from the exact emitted rule IDs so every
# result references a descriptor that actually exists in the report.
_OWASP_2025_TITLES: dict[str, str] = {
    "LLM01": "Prompt Injection",
    "LLM02": "Sensitive Information Disclosure",
    "LLM03": "Supply Chain",
    "LLM04": "Data and Model Poisoning",
    "LLM05": "Improper Output Handling",
    "LLM06": "Excessive Agency",
    "LLM07": "System Prompt Leakage",
    "LLM08": "Vector and Embedding Weaknesses",
    "LLM09": "Misinformation",
    "LLM10": "Unbounded Consumption",
}


def _rule_descriptor(finding: dict[str, Any]) -> dict[str, Any]:
    rule_id = str(finding.get("rule_id", "UNKNOWN"))
    owasp_id = str(finding.get("owasp_llm_id", "")).strip()
    detector = str(finding.get("detector", "")).strip() or "detector"
    category = _OWASP_2025_TITLES.get(owasp_id, "Security Finding")
    tags = ["security", "OWASP"]
    if owasp_id:
        tags.append(owasp_id)
    return {
        "id": rule_id,
        "name": rule_id.replace("-", "_"),
        "shortDescription": {"text": f"{category}: {rule_id}"},
        "fullDescription": {
            "text": (
                f"Finding emitted by {detector}. "
                + (
                    f"Mapped to OWASP Top 10 for LLM Applications 2025 {owasp_id}: {category}."
                    if owasp_id
                    else "No OWASP category is claimed for this rule."
                )
            )
        },
        "helpUri": "https://genai.owasp.org/llm-top-10/",
        "properties": {"tags": tags},
    }


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

    rules_by_id: dict[str, dict[str, Any]] = {}
    for finding in findings:
        rule_id = str(finding.get("rule_id", "UNKNOWN"))
        rules_by_id.setdefault(rule_id, _rule_descriptor(finding))
    rules_to_emit = list(rules_by_id.values())

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

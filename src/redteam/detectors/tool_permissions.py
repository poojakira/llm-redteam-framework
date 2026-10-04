"""Deterministic OWASP 2025 LLM06 excessive-agency checks for agent tool calls.

This module does not judge whether a tool action is semantically correct. It
enforces the permission boundary supplied by the caller: only declared tools
may be used, and explicitly denied argument keys may not be supplied.

The design is intentionally deterministic so it can be used in CI and at an
agent execution boundary without a second LLM.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class ToolPermissionBoundaryDetector:
    """Validate tool calls against an explicit least-privilege policy."""

    def scan(
        self,
        tool_calls: Sequence[Mapping[str, Any]],
        allowed_tools: Sequence[str],
        denied_argument_keys: Mapping[str, Sequence[str]] | None = None,
    ) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        allowed = {name.strip() for name in allowed_tools if name.strip()}
        denied = denied_argument_keys or {}

        if tool_calls and not allowed:
            findings.append(
                {
                    "rule_id": "LLM06-UNDECLARED-TOOLS",
                    "severity": "HIGH",
                    "message": (
                        "Tool calls were supplied without an explicit allowed_tools boundary. "
                        "Declare the least-privilege tool set before enabling agent actions."
                    ),
                }
            )

        for index, raw_call in enumerate(tool_calls):
            name = str(raw_call.get("name", "")).strip()
            arguments = raw_call.get("arguments", {})
            if not name:
                findings.append(
                    {
                        "rule_id": "LLM06-MALFORMED-TOOL-CALL",
                        "severity": "HIGH",
                        "message": f"Tool call {index} has no valid tool name.",
                    }
                )
                continue

            if name not in allowed:
                findings.append(
                    {
                        "rule_id": "LLM06-TOOL-OUTSIDE-BOUNDARY",
                        "severity": "HIGH",
                        "message": (
                            f"Tool call {index} requests {name!r}, which is outside "
                            "the declared allowed_tools boundary."
                        ),
                    }
                )
                continue

            if not isinstance(arguments, Mapping):
                findings.append(
                    {
                        "rule_id": "LLM06-MALFORMED-TOOL-ARGUMENTS",
                        "severity": "HIGH",
                        "message": f"Tool call {index} arguments must be an object.",
                    }
                )
                continue

            blocked_keys = {key for key in denied.get(name, ()) if key}
            present = sorted(blocked_keys.intersection(str(key) for key in arguments))
            if present:
                findings.append(
                    {
                        "rule_id": "LLM06-DENIED-TOOL-ARGUMENT",
                        "severity": "HIGH",
                        "message": (
                            f"Tool call {index} to {name!r} supplies explicitly denied "
                            f"argument key(s): {', '.join(present)}."
                        ),
                    }
                )

        return findings

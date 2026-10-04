from redteam.detectors.tool_permissions import ToolPermissionBoundaryDetector


def test_allows_declared_read_only_tool():
    detector = ToolPermissionBoundaryDetector()
    findings = detector.scan(
        tool_calls=[{"name": "search_docs", "arguments": {"query": "incident runbook"}}],
        allowed_tools=["search_docs"],
    )
    assert findings == []


def test_blocks_tool_outside_declared_boundary():
    detector = ToolPermissionBoundaryDetector()
    findings = detector.scan(
        tool_calls=[
            {
                "name": "send_email",
                "arguments": {"to": "external@example.invalid", "body": "export"},
            }
        ],
        allowed_tools=["search_docs"],
    )
    assert {item["rule_id"] for item in findings} == {"LLM06-TOOL-OUTSIDE-BOUNDARY"}


def test_fails_closed_when_tool_calls_have_no_policy():
    detector = ToolPermissionBoundaryDetector()
    findings = detector.scan(
        tool_calls=[{"name": "delete_resource", "arguments": {"id": "prod-1"}}],
        allowed_tools=[],
    )
    rule_ids = {item["rule_id"] for item in findings}
    assert "LLM06-UNDECLARED-TOOLS" in rule_ids
    assert "LLM06-TOOL-OUTSIDE-BOUNDARY" in rule_ids


def test_blocks_explicitly_denied_high_impact_argument():
    detector = ToolPermissionBoundaryDetector()
    findings = detector.scan(
        tool_calls=[
            {
                "name": "send_email",
                "arguments": {
                    "to": "approved@example.invalid",
                    "bcc": "unapproved@example.invalid",
                    "body": "status",
                },
            }
        ],
        allowed_tools=["send_email"],
        denied_argument_keys={"send_email": ["bcc"]},
    )
    assert [item["rule_id"] for item in findings] == ["LLM06-DENIED-TOOL-ARGUMENT"]

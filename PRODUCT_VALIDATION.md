# Product Validation

## Product boundary
Offline and endpoint-facing adversarial evaluation for prompt injection, sensitive-data leakage signals, poisoned retrieval context, and deterministic agent tool-permission boundaries.

## Real-world validation ladder
1. Grouped-template regression.
2. Novel-phrasing OOD benchmark with no train/fixture overlap.
3. Published/structural benchmark corpus kept separate from the OOD score.
4. Endpoint-scanner contract tests for timeouts, body limits, authentication, malformed targets, and OWASP 2025 LLM06 tool-call permission boundaries.
5. Standards-integrity gate: API findings, SARIF, threat model, and README must use the same OWASP Top 10 for LLM Applications 2025 IDs.
6. External pilot against a real agent/LLM application with operator approval.

## Release gates
- Never promote random-split F1 as the generalization result.
- OOD F1 is the primary generalization regression metric and must remain separately reported.
- Live-provider testing is optional because it can cost money and change over time; offline CI remains deterministic.

- Tool-boundary success proves only that declared tool/argument permissions were respected; it does not prove the permitted action was semantically correct.
- SARIF serialization is reporting, not an OWASP LLM05 output-sanitization control.

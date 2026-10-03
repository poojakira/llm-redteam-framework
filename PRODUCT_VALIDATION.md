# Product Validation

## Product boundary
Offline and endpoint-facing adversarial evaluation for prompt-injection and related LLM security controls.

## Real-world validation ladder
1. Grouped-template regression.
2. Novel-phrasing OOD benchmark with no train/fixture overlap.
3. Published/structural benchmark corpus kept separate from the OOD score.
4. Endpoint-scanner contract tests for timeouts, body limits, authentication, and malformed targets.
5. External pilot against a real agent/LLM application with operator approval.

## Release gates
- Never promote random-split F1 as the generalization result.
- OOD F1 is the primary generalization regression metric and must remain separately reported.
- Live-provider testing is optional because it can cost money and change over time; offline CI remains deterministic.

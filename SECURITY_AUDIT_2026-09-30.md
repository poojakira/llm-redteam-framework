# Security Audit — 2026-09-30

## Scope
Initial pre-remediation review of the current `main` branch.

## Runtime surface
Authenticated FastAPI scanning API with Prometheus metrics.

## Verified controls
- API authentication fails closed.
- YAML configuration uses safe loading.
- Input character counts, document counts, concurrency, and scan timeout are bounded.
- Generic catch-all server errors are returned while details are logged server-side.
- Metrics require authentication.
- No confirmed live API key was found in the current main branch.

## Findings to remediate/verify
1. Current limiter is in-memory; require a shared production limiter for multi-replica deployments.
2. Avoid using one shared API-key hash as the only rate-limit identity when multiple clients share a key.
3. Add request-byte limits before JSON parsing.
4. Bound `session_id` and response string lengths directly in Pydantic fields.
5. Add critical alerts for repeated auth failures, timeouts, scan errors, and saturation.
6. Add health-gated blue/green/rollback guidance.

## Not applicable
SQL tenant isolation and password reset.

<!-- repo-verification:start -->
## Verification update — 2026-09-30

- **Scope:** Account-wide `poojakira` repository pass covering source/configuration, CI/release workflows, security-hygiene gates, dependency/SAST controls, and documentation consistency.
- **Remediation:** Applied safe Ruff fixes/formatting, pinned CI/security/release/container actions to immutable revisions, and reran the security scans.
- **Verification state:** CI, Production Gate, Security Hygiene, Documentation Integrity, both LLM Security Scan workflows, and Container Release completed successfully after remediation.
- **Security note:** The malicious prompt corpus is intentionally adversarial test data and was retained; detections in that corpus are expected evaluation behavior.
- **Evidence boundary:** This update records repository and GitHub Actions evidence observed during the pass. It is not a claim of independent penetration testing, production deployment, or zero residual risk.
<!-- repo-verification:end -->

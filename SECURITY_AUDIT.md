# Security Audit — llm-redteam-framework

**Audit date:** 2026-09-29  
**Scope:** FastAPI scanner service, live endpoint scanner, authentication, input limits, rate limiting, network requests, containers, CI, and error handling.

## Findings captured before this remediation pass

| ID | Severity | Finding | Status |
|---|---|---|---|
| LLM-001 | High | Live endpoint scanning now validates scheme, userinfo, DNS resolution and resolved IP ranges before credential forwarding; private/local targets require explicit `allow_private=True`. | Fixed |
| LLM-002 | Medium | HTTP middleware now enforces a bounded raw request size before scan handling. | Fixed |
| LLM-003 | Medium | The limiter key now incorporates the request peer together with the configured API key, preventing one peer from consuming the entire shared-key bucket. Multi-replica deployments still require a shared limiter. | Fixed |
| LLM-004 | Info | Generic server errors are already returned by the API and detailed exceptions are logged server-side. | Verified |

## Existing controls verified

- Fail-closed 32+ character API key.
- Constant-time key comparison.
- Prompt/context count and total-character bounds.
- Concurrency semaphore and scan timeout.
- Authenticated metrics.
- Generic unhandled-error response.
- Non-root container.
- Secret-hygiene CI.

## Verification plan

Constrain endpoint destinations, add raw body limits and fairer throttling, then run the full CI/security workflows.

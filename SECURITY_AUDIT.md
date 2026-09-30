# Security Audit — llm-redteam-framework

**Audit date:** 2026-09-29  
**Scope:** FastAPI scanner service, live endpoint scanner, authentication, input limits, rate limiting, network requests, containers, CI, and error handling.

## Findings captured before this remediation pass

| ID | Severity | Finding | Status |
|---|---|---|---|
| LLM-001 | High | Live endpoint scanning accepts an arbitrary base URL and forwards the supplied API key to that host. Without an explicit private-network opt-in this can enable SSRF/credential forwarding. | Open |
| LLM-002 | Medium | The API bounds parsed text but does not impose a raw request-byte limit before body parsing. | Open |
| LLM-003 | Medium | The in-memory limiter is keyed only by the configured service API key, so one caller can exhaust a shared-key quota for all clients. | Open |
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

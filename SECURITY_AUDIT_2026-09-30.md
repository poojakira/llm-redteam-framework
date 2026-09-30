# Security review, 30 September 2026

Reviewed baseline: `891e0cc5e82b099987f44990bb69a575d2750dbe`. Source review and focused regression verification; this is not proof that all vulnerabilities are absent.

## Fixes and reviewed controls

Streaming body limit rejects chunked overflow before parsing. Credentialed live scans reject redirects and cap responses at 1 MiB. UTF-8 byte comparisons reject non-ASCII invalid API keys without comparison errors. Runtime dependency floors exclude audited vulnerable Starlette/AnyIO versions.

## Verification

175 passed; one optional ATT&CK package test skipped. Tests ran in an isolated Python 3.12 environment. FastAPI TestClient required execution outside the default sandbox; a minimal unchanged app reproduced the sandbox deadlock. Final installed-environment pip-audit reported no known vulnerabilities. This does not cover every optional dependency, every container image, or arbitrary older environments allowed by broad dependency bounds.

## Secret history review

16 history matches were synthetic detector/API fixtures and documentation examples. No tracked environment or private-key paths found in fetched history. Gitleaks classifications are pattern matches, not provider validity checks. No provider key was tested or revoked, and fetched Git refs do not include every cached/forked copy. `.env` and local credential patterns remain ignored; example files must contain placeholders only.

## Deployment and remaining limits

The API key authorizes the same scan/metrics operations for every holder; there is no tenant or role policy. Rate limits are per process and require a shared ingress limiter for multiple workers. DNS validation is not connection-pinned: use an egress firewall for live endpoint scans. Timeout cancellation does not terminate running detector threads; production workloads need killable worker isolation.

<!-- hardening-followup-20260930:start -->
## Follow-up hardening — 2026-09-30

- GitHub Actions were hardened on `main`: checkout credentials are not persisted, build-provenance actions were changed from floating tags to immutable commit SHAs, and the obsolete one-time write-enabled formatter workflow was removed.
- `scripts/workflow_security_scan.py` now enforces immutable external action references, blocks `pull_request_target` and `workflow_run`, requires non-persisted checkout credentials, and rejects pipe-to-shell execution in workflows.
- Existing pickle model loading remains fail-closed by default: deserialization requires an explicit `trusted=True` after checksum verification, while documentation correctly notes that a colocated checksum is not provenance.
- Remaining tenant authorization, multi-worker shared rate limiting, egress firewalling, and killable-worker isolation are deployment/architecture limits and are not represented as completed controls.
<!-- hardening-followup-20260930:end -->

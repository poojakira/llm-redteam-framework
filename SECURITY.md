# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (main) | ✅ |
| Older releases | ❌  --  please upgrade |

## Reporting a Vulnerability

To report a security vulnerability in this tool, **do not open a public GitHub issue**.

Please email: **security@[your-email-here]**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact (what an attacker could achieve)
- Any suggested mitigations

**Expected response time:** Acknowledgement within 72 hours. Patch timeline depends on severity  --  CRITICAL issues are prioritized within 7 days.

This project follows **coordinated disclosure**: please allow reasonable time for a fix before public disclosure. We will credit reporters in the CHANGELOG unless you prefer to remain anonymous.

## Scope

In scope for this tool:
- Vulnerabilities in the scanner itself that allow an attacker to bypass detection
- Code execution vulnerabilities triggered by processing crafted input prompts
- Vulnerabilities in the FastAPI service endpoints (if applicable)
- Dependency vulnerabilities in direct dependencies (report via the email above or open a private advisory via GitHub)

Out of scope:
- Findings in transitive dependencies not exploitable via this tool's attack surface
- Performance issues that are not exploitable
- Issues in the underlying scikit-learn/numpy libraries (report to those projects directly)
- False positive / false negative rates  --  these are limitations, not vulnerabilities; open a regular issue

## Security Assumptions

This tool assumes:
- Input prompts are provided by a trusted caller (not directly from end users without sanitization)
- The scanning service is not exposed publicly without authentication
- Log output (which may contain flagged prompt fragments if `log_prompt_content: true`) is stored securely

See [THREAT_MODEL.md](THREAT_MODEL.md) for the full threat model of the tool itself.

<!-- credential-response:start -->
## Credential and secret handling

- Real API keys, tokens, passwords, private keys, cloud credentials, and populated environment files must never be committed.
- Local users must create their own `.env` from the repository's safe template when environment variables are needed, and must supply **their own** credentials. CI/CD credentials belong in GitHub repository/environment secrets or an external secret manager, not in source or workflow YAML.
- If a real credential is exposed, treat it as compromised even if the commit is quickly deleted. **Revoke or rotate the credential at its provider first.** Then remove it from the current tree, reachable Git history, logs/artifacts, examples, screenshots, and documentation as applicable.
- Rewriting Git history or deleting a file does **not** revoke a credential. Provider-side rotation/revocation is required.
- Placeholder/test credentials must be clearly marked and must not be valid for real services.
<!-- credential-response:end -->

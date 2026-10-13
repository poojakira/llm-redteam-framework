# Historical runs

The following sections were moved verbatim from the starting README during the 2026-10-13 audit. Confidence: partially verified as committed documentation; underlying run logs were not independently recovered. Missing commands, environments, dates or commits remain unknown unless included in each entry. None is a current execution claim.

## Verified Snapshot

Reproduced on current `main` (Python 3.12). Grouped/OOD figures are pinned in tests.

| Metric | Current verified result |
|---|---:|
| Tests | 183 collected — 182 passed, 1 skipped |
| Statement coverage | 94.22% |
| Attack categories | 6 (+ benign control) |
| Grouped-split F1 (in-distribution) | 0.9714 |
| Novel-phrasing OOD F1 | 0.7188 (precision 0.5897, recall 0.92) |


## Verification update — 2026-09-30

- **Scope:** Account-wide `poojakira` repository pass covering source/configuration, CI/release workflows, security-hygiene gates, dependency/SAST controls, and documentation consistency.
- **Remediation:** Applied safe Ruff fixes/formatting, pinned CI/security/release/container actions to immutable revisions, and reran the security scans.
- **Verification state:** CI, Production Gate, Security Hygiene, Documentation Integrity, both LLM Security Scan workflows, and Container Release completed successfully after remediation.
- **Security note:** The malicious prompt corpus is intentionally adversarial test data and was retained; detections in that corpus are expected evaluation behavior.
- **Evidence boundary:** This update records repository and GitHub Actions evidence observed during the pass. It is not a claim of independent penetration testing, production deployment, or zero residual risk.
<!-- repo-verification:end -->


## Verification checkpoint — 2026-09-30

- **Status:** VERIFIED GREEN FOR THE LISTED REPOSITORY GATES
- **Evidence:** CI, Security Hygiene, Documentation Integrity, Production Gate, both LLM Security Scan workflows, and Container Release completed successfully on the last verified main revision.
- **Boundary:** This is dated repository/Actions evidence, not a claim of zero vulnerabilities, external penetration testing, or universal production readiness.



### Results

| Metric | Random Split (In-Distribution) | Grouped Split (OOD Templates) | Structural Fixtures | Novel-Phrasing OOD |
|--------|-------------------------------|-------------------------------|---------------------|--------------------|
| F1 Score | 1.00 | 0.9714 | 0.98 | **0.7188** |
| Precision | 1.00 | 0.94 | ~0.98 | 0.5897 |
| Recall | 1.00 | 1.00 | ~0.98 | 0.92 |
| False Positive Rate | 0.0% | 7.9% | ~1% | 64% (16/25) |

*Grouped/random measured with seed=42, corpus-seed=20240713, test-size=0.3 (pinned in `tests/test_eval.py`). Structural fixtures from `benchmarks/external_validation.py`. Novel-phrasing OOD from `benchmarks/ood_novel_phrasings.py` (pinned in `tests/test_ood_benchmark.py`). The novel-phrasing column is the honest generalization figure — structural fixtures still contain the markers the model memorised.*

| Additional | Value |
|------------|-------|
| Attack Categories | 6 |
| OWASP 2025 Coverage | Partial LLM01, LLM02, LLM04, LLM06 |
| Test coverage | See [current local verification](docs/verification-2026-10-13.md). |

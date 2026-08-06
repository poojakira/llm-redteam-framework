# Security Audit — llm-redteam-framework

**Audit date:** 2026-08-06  
**Auditor:** Automated hardening agent (kiro/llm_redteam session)  
**Branch:** agent/security-hardening-v1  
**Scope:** `src/redteam/detector/detector.py`, `src/redteam/api/app.py`, `.github/workflows/ci.yml`, `pyproject.toml`

---

## Purpose

This document records findings from a Strictness-10 security review of the
`llm-redteam-framework` repository. All findings are grounded in code actually
read during this session. No speculative or invented vulnerabilities are listed.

---

## Implemented Capabilities (as observed)

| Component | What is actually implemented |
|-----------|------------------------------|
| `RedTeamDetector` (detector.py) | TF-IDF char n-gram + LogisticRegression binary classifier. Serialises with `pickle.dumps`; deserialises with `pickle.loads` guarded by SHA-256 integrity check AND an explicit `trusted=True` gate. |
| `save()` | Writes `.pkl` + colocated `.pkl.sha256` (hex digest of pickle bytes). |
| `load()` | Reads checksum file; computes SHA-256 of bytes on disk; raises `ValueError` on mismatch; raises `ValueError` if `trusted=False` (default); only then calls `pickle.loads`. |
| API (`app.py`) | FastAPI service with `/health`, `/metrics` (Prometheus), `/scan` (PII + RAG + embedding detectors). `/scan` catches exceptions internally and re-raises as `HTTPException(detail=str(exc))`. |
| CI (`ci.yml`) | GitHub Actions: lint (ruff) → test (3×Python) → CodeQL. Most `uses:` steps are SHA-pinned. `permissions: contents: read` is set at workflow level. |

---

## Critical Findings

_None._

No remote code execution paths, no unauthenticated write endpoints, no
secret/credential material in tracked files were observed.

---

## High Findings

### H-01 — `/metrics` endpoint has no access control

**File:** `src/redteam/api/app.py`, line ~56  
**Code:**
```python
@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus metrics scrape endpoint (internal network only)."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```
**Risk:** The comment says "internal network only" but the application itself
enforces nothing. If the service is ever reachable on a non-internal interface,
any client can scrape counters and histograms that reveal detection rates,
request volumes, and timing distributions — information useful to an adversary
profiling detection sensitivity.  
**Remediation:** Restrict `/metrics` at the network/ingress layer (preferred) or
add a bearer-token or IP allowlist middleware. Document the network-level
requirement in deployment runbooks.

---

### H-02 — `/scan` exception handler leaks internal error detail

**File:** `src/redteam/api/app.py`, lines ~138-141  
**Code (before fix):**
```python
except Exception as exc:
    SCAN_REQUESTS.labels(status="error").inc()
    raise HTTPException(status_code=500, detail=str(exc)) from exc
```
**Risk:** `str(exc)` can expose internal paths, detector class names, library
stack details, or data fragments present in the exception message. This is an
information-disclosure finding at HIGH severity because the API is designed to
process potentially sensitive prompt/response pairs.  
**Remediation:** Replace `detail=str(exc)` with a generic message. Log the real
exception server-side. **Fixed in this PR** — see `src/redteam/api/app.py`.

---

## Medium Findings

### M-01 — Floating `actions/checkout@v4` tag in CI test job

**File:** `.github/workflows/ci.yml`, `test` job, step "Checkout attack-v19-core"  
**Code (before fix):**
```yaml
uses: actions/checkout@v4
```
**Risk:** A tag is mutable; a supply-chain compromise of the `actions/checkout`
repo could silently swap the action. All other `checkout` invocations in the
file are already pinned to `11bd71901bbe5b1630ceea73d27597364c9af683`.  
**Remediation:** Pin to the same SHA. **Fixed in this PR.**

---

### M-02 — No `pip-audit` step in CI

**Risk:** Transitive dependency vulnerabilities are not automatically surfaced.
Given that the framework processes untrusted prompt/response data, a
dependency with a known CVE (e.g. in `scikit-learn`, `numpy`, or `fastapi`)
could be introduced silently.  
**Remediation:** Add `pip-audit` as a CI step. **Fixed in this PR** — added to
the `test` job after `pip install`.

---

### M-03 — `pickle` used for model serialisation (design-level note)

**File:** `src/redteam/detector/detector.py`  
**Observation:** `pickle.dumps` / `pickle.loads` are used. The existing
`load()` implementation already mitigates the primary exploit path with:
1. SHA-256 integrity verification before deserialisation.
2. Explicit `trusted=True` flag required by the caller.
3. Payload schema validation (`isinstance(payload, dict)` with required keys).

**No code change was made here.** The existing guard is functionally correct.
The medium-severity note is retained because pickle's safety fundamentally
depends on the integrity of the checksum file, which must itself be
stored/distributed via a trusted channel. Teams should consider migrating to
`safetensors` or ONNX for the sklearn pipeline if a future version supports it,
or at minimum verify the `.sha256` file arrives via a separate authenticated
channel from the `.pkl`.

---

## Unsupported Claims

The following metrics appear in documentation and require additional context:

| Claim | Source | Status |
|-------|--------|--------|
| F1 = 0.70 on out-of-distribution grouped split | README, `results/scan_metrics.json` | ⚠️ PARTIALLY VERIFIED — `scan_metrics.json` records this value; `evidence/generated/llm_internal_evidence.json` shows F1=0.971 on grouped split with internal corpus. The 0.70 OOD number is referenced but the exact OOD evaluation script is not committed as a reproducible artifact. |
| F1 = 0.93 on curated in-distribution split | README | ⚠️ PARTIALLY VERIFIED — `scan_metrics.json` records `f1_curated: 0.93`; no independent reproduction script committed. |
| F1 >= 0.85 on InjectionBench/JailbreakBench style fixtures | `tests/test_benchmark_f1.py` | ✅ VERIFIED — test asserts F1 >= 0.85 on committed fixture data with deterministic seed. Runnable with `pytest tests/test_benchmark_f1.py -v`. |

`evidence_policy.json` (added in this PR) provides a template that CI should
populate to make these claims reproducible and auditable.

---

## Remediation Plan

| ID | Priority | Change | Status |
|----|----------|--------|--------|
| H-02 | HIGH | Replace `detail=str(exc)` with generic error in `/scan` exception handler; add global exception handler returning `{"error": "internal error"}` | **Done — this PR** |
| M-01 | MEDIUM | Pin floating `actions/checkout@v4` to SHA `11bd71901bbe5b1630ceea73d27597364c9af683` | **Done — this PR** |
| M-02 | MEDIUM | Add `pip-audit` step to CI test job | **Done — this PR** |
| H-01 | HIGH | Enforce network-level restriction on `/metrics` (infrastructure task, not code) | Open — deploy runbook required |
| M-03 | LOW/MEDIUM | Consider migrating to non-executable serialisation format long-term | Open — future work |
| — | — | Add `evidence_policy.json` template for reproducible benchmark claims | **Done — this PR** |

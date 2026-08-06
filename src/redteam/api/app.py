"""
src/redteam/api/app.py
──────────────────────────────────────────────────────────────────────────────
FastAPI service for the LLM red-team framework.

Endpoints
---------
POST /scan   — run all detectors against a prompt/response pair
GET  /health — liveness check
GET  /metrics — Prometheus metrics (internal)

Usage
-----
    uvicorn src.redteam.api.app:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field

from redteam.detectors.pii_leakage import PIILeakageDetector
from redteam.detectors.rag_poisoning import RAGPoisoningDetector
from redteam.detectors.embedding_similarity import EmbeddingSimilarityDetector
from redteam.output.sarif import findings_to_sarif

app = FastAPI(
    title="LLM Red-Team Framework",
    version="1.0.0",
    description="Scan LLM prompt/response pairs for security findings.",
)

# ── Prometheus metrics ─────────────────────────────────────────────────────────
SCAN_REQUESTS = Counter("scan_requests_total", "Total /scan requests", ["status"])
FINDINGS_TOTAL = Counter("findings_total", "Findings by severity", ["severity"])
SCAN_LATENCY = Histogram(
    "scan_latency_seconds",
    "End-to-end scan latency",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

# ── Detector singletons ────────────────────────────────────────────────────────
_pii_detector = PIILeakageDetector()
_rag_detector = RAGPoisoningDetector()
_emb_detector = EmbeddingSimilarityDetector()


# ── Request / response models ──────────────────────────────────────────────────
class ScanRequest(BaseModel):
    prompt: str = Field(..., description="The user prompt sent to the LLM.")
    response: str = Field("", description="The LLM response (optional).")
    context_docs: list[str] = Field(
        default_factory=list,
        description="RAG context documents injected alongside the prompt.",
    )
    session_id: str = Field("", description="Optional session identifier for canary tracking.")


class Finding(BaseModel):
    rule_id: str
    severity: str          # CRITICAL | HIGH | MEDIUM | LOW | NOTE
    message: str
    detector: str
    owasp_llm_id: str = ""


class ScanResponse(BaseModel):
    scan_id: str
    findings: list[Finding]
    sarif: dict[str, Any]
    blocked: bool          # True if any HIGH or CRITICAL finding present
    duration_ms: float


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> JSONResponse:
    """Liveness check. Returns 200 when service is ready."""
    return JSONResponse({"status": "ok", "service": "llm-redteam-framework"})


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus metrics scrape endpoint (internal network only)."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/scan", response_model=ScanResponse)
async def scan(req: ScanRequest, request: Request) -> ScanResponse:
    """
    Run all detectors against a prompt/response pair.

    Returns a list of findings and a SARIF 2.1.0 document.
    Sets ``blocked=True`` if any HIGH or CRITICAL finding is present.
    """
    import uuid

    t0 = time.perf_counter()
    scan_id = str(uuid.uuid4())
    all_findings: list[Finding] = []

    try:
        # ── PII / secret leakage ───────────────────────────────────────────
        pii_results = _pii_detector.scan(req.prompt + "\n" + req.response)
        for r in pii_results:
            all_findings.append(
                Finding(
                    rule_id=r["rule_id"],
                    severity=r["severity"],
                    message=r["message"],
                    detector="pii_leakage",
                    owasp_llm_id="LLM06",
                )
            )

        # ── RAG poisoning ──────────────────────────────────────────────────
        if req.context_docs:
            rag_results = _rag_detector.scan(req.prompt, req.context_docs)
            for r in rag_results:
                all_findings.append(
                    Finding(
                        rule_id=r["rule_id"],
                        severity=r["severity"],
                        message=r["message"],
                        detector="rag_poisoning",
                        owasp_llm_id="LLM07",
                    )
                )

        # ── Embedding similarity (prompt injection patterns) ───────────────
        emb_results = _emb_detector.scan(req.prompt)
        for r in emb_results:
            all_findings.append(
                Finding(
                    rule_id=r["rule_id"],
                    severity=r["severity"],
                    message=r["message"],
                    detector="embedding_similarity",
                    owasp_llm_id="LLM01",
                )
            )

        blocked = any(f.severity in ("HIGH", "CRITICAL") for f in all_findings)
        sarif_doc = findings_to_sarif(scan_id, [f.model_dump() for f in all_findings])
        duration_ms = (time.perf_counter() - t0) * 1000

        SCAN_REQUESTS.labels(status="success").inc()
        for f in all_findings:
            FINDINGS_TOTAL.labels(severity=f.severity).inc()
        SCAN_LATENCY.observe(duration_ms / 1000)

        return ScanResponse(
            scan_id=scan_id,
            findings=all_findings,
            sarif=sarif_doc,
            blocked=blocked,
            duration_ms=round(duration_ms, 2),
        )

    except Exception as exc:  # noqa: BLE001
        SCAN_REQUESTS.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

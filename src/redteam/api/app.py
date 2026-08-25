"""
src/redteam/api/app.py
──────────────────────────────────────────────────────────────────────────────
FastAPI service for the LLM red-team framework.

Endpoints
---------
POST /scan    --  run all detectors against a prompt/response pair
GET  /health  --  liveness check
GET  /metrics  --  Prometheus metrics (internal)

Usage
-----
    uvicorn src.redteam.api.app:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field

from redteam.detectors.embedding_similarity import EmbeddingSimilarityDetector
from redteam.detectors.pii_leakage import PIILeakageDetector
from redteam.detectors.rag_poisoning import RAGPoisoningDetector
from redteam.output.sarif import findings_to_sarif

logger = logging.getLogger(__name__)

# ── Load config for rate limiting / input validation ───────────────────────────
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "llm-security-config.yaml")
try:
    with open(_CONFIG_PATH) as _f:
        _config = yaml.safe_load(_f)
except FileNotFoundError:
    _config = {}

_RATE_LIMIT = _config.get("rate_limiting", {}).get("max_requests_per_minute", 60)
_MAX_PROMPT_LENGTH = _config.get("rate_limiting", {}).get("max_prompt_length_chars", 32768)

# ── In-memory token-bucket rate limiter (per-IP, no external deps) ─────────────
_request_log: dict[str, list[float]] = defaultdict(list)


def _is_rate_limited(client_ip: str) -> bool:
    """Return True if client_ip has exceeded _RATE_LIMIT requests in the last 60s."""
    now = time.time()
    window_start = now - 60.0
    # Prune old entries
    _request_log[client_ip] = [ts for ts in _request_log[client_ip] if ts > window_start]
    if len(_request_log[client_ip]) >= _RATE_LIMIT:
        return True
    _request_log[client_ip].append(now)
    return False


# ── API Key authentication ─────────────────────────────────────────────────────
_API_KEY = os.environ.get("REDTEAM_API_KEY", "")


def _check_api_key(request: Request) -> str | None:
    """Validate API key if configured. Returns error message or None on success."""
    if not _API_KEY:
        return None  # Auth disabled, allow all
    provided = request.headers.get("X-API-Key", "")
    if provided != _API_KEY:
        return "Invalid or missing API key"
    return None


app = FastAPI(
    title="LLM Red-Team Framework",
    version="1.0.0",
    description="Scan LLM prompt/response pairs for security findings.",
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler: log full details server-side, return generic message to client.

    Deliberately omits traceback and exception text from the response body to
    prevent information disclosure (CWE-209).
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "internal error"})


# ── Prometheus metrics ─────────────────────────────────────────────────────────
# Use try/except to survive module reloads (e.g., during testing with importlib.reload).


def _get_or_create_metric(cls, name, *args, **kwargs):
    """Return an existing metric or create a new one, surviving reloads."""
    try:
        return cls(name, *args, **kwargs)
    except ValueError:
        # Already registered — retrieve the existing collector.
        from prometheus_client import REGISTRY as _REG

        collector = _REG._names_to_collectors.get(name)
        if collector is not None:
            return collector
        raise


SCAN_REQUESTS = _get_or_create_metric(
    Counter, "scan_requests_total", "Total /scan requests", ["status"]
)
FINDINGS_TOTAL = _get_or_create_metric(
    Counter, "findings_total", "Findings by severity", ["severity"]
)
SCAN_LATENCY = _get_or_create_metric(
    Histogram,
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
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW | NOTE
    message: str
    detector: str
    owasp_llm_id: str = ""


class ScanResponse(BaseModel):
    scan_id: str
    findings: list[Finding]
    sarif: dict[str, Any]
    blocked: bool  # True if any HIGH or CRITICAL finding present
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
async def scan(req: ScanRequest, request: Request, response: Response) -> ScanResponse:
    """
    Run all detectors against a prompt/response pair.

    Returns a list of findings and a SARIF 2.1.0 document.
    Sets ``blocked=True`` if any HIGH or CRITICAL finding is present.
    """
    import uuid

    # ── Auth check ─────────────────────────────────────────────────────────
    auth_error = _check_api_key(request)
    if auth_error:
        raise HTTPException(status_code=401, detail=auth_error)
    if not _API_KEY:
        response.headers["X-Auth-Status"] = "disabled - set REDTEAM_API_KEY to enable"

    # ── Rate limiting ──────────────────────────────────────────────────────
    client_ip = request.client.host if request.client else "unknown"
    if _is_rate_limited(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {_RATE_LIMIT} requests/minute",
        )

    # ── Input length validation ────────────────────────────────────────────
    if len(req.prompt) > _MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"Prompt too long: {len(req.prompt)} chars exceeds max {_MAX_PROMPT_LENGTH}",
        )

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
        logger.exception("Scan error for scan_id=%s", scan_id)
        raise HTTPException(status_code=500, detail="internal error") from exc

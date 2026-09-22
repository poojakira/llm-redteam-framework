"""
src/redteam/api/app.py
──────────────────────────────────────────────────────────────────────────────
FastAPI service for the LLM red-team framework.

Endpoints
---------
POST /scan    --  run all detectors against a prompt/response pair
GET  /health  --  liveness check
GET  /metrics --  Prometheus metrics (authenticated)

Authentication
--------------
``REDTEAM_API_KEY`` is required for protected endpoints. The service fails
closed when the secret is missing. Local development should set an explicit
development-only key rather than relying on an anonymous production mode.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import os
import time
from collections import defaultdict
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from redteam.detectors.embedding_similarity import EmbeddingSimilarityDetector
from redteam.detectors.pii_leakage import PIILeakageDetector
from redteam.detectors.rag_poisoning import RAGPoisoningDetector
from redteam.output.sarif import findings_to_sarif

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "llm-security-config.yaml")
try:
    with open(_CONFIG_PATH) as _f:
        _config = yaml.safe_load(_f)
except FileNotFoundError:
    _config = {}

_RATE_LIMIT = _config.get("rate_limiting", {}).get("max_requests_per_minute", 60)
_MAX_PROMPT_LENGTH = _config.get("rate_limiting", {}).get("max_prompt_length_chars", 32768)
_MAX_CONTEXT_DOCS = _config.get("rate_limiting", {}).get("max_context_documents", 64)
_MAX_TOTAL_INPUT_CHARS = _config.get("rate_limiting", {}).get("max_total_input_chars", 131072)
_request_log: dict[str, list[float]] = defaultdict(list)
_SCAN_TIMEOUT_SECONDS = float(os.environ.get("REDTEAM_SCAN_TIMEOUT_SECONDS", "30"))
_MAX_CONCURRENT_SCANS = int(os.environ.get("REDTEAM_MAX_CONCURRENT_SCANS", "8"))
if _SCAN_TIMEOUT_SECONDS <= 0:
    raise RuntimeError("REDTEAM_SCAN_TIMEOUT_SECONDS must be positive")
if _MAX_CONCURRENT_SCANS < 1 or _MAX_CONCURRENT_SCANS > 128:
    raise RuntimeError("REDTEAM_MAX_CONCURRENT_SCANS must be between 1 and 128")
_scan_slots = asyncio.Semaphore(_MAX_CONCURRENT_SCANS)


def _is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - 60.0
    _request_log[client_ip] = [ts for ts in _request_log[client_ip] if ts > window_start]
    if len(_request_log[client_ip]) >= _RATE_LIMIT:
        return True
    _request_log[client_ip].append(now)
    return False


# Authentication is fail-closed. An operator must explicitly configure a key,
# including in local development. This avoids an accidental anonymous service
# when a deployment forgets its secret.
_API_KEY = os.environ.get("REDTEAM_API_KEY", "")
_ENFORCEMENT_MODE = os.environ.get("REDTEAM_ENFORCEMENT_MODE", "shadow").strip().lower()
if _ENFORCEMENT_MODE not in {"shadow", "block"}:
    raise RuntimeError("REDTEAM_ENFORCEMENT_MODE must be 'shadow' or 'block'")


def _check_api_key(request: Request) -> str | None:
    """Return an error when authentication is missing or invalid."""
    if len(_API_KEY) < 32:
        return "API authentication is not configured with a sufficiently strong key"
    provided = request.headers.get("X-API-Key", "")
    if not provided or not hmac.compare_digest(provided, _API_KEY):
        return "Invalid or missing API key"
    return None


app = FastAPI(
    title="LLM Red-Team Framework",
    version="1.0.0",
    description="Scan LLM prompt/response pairs for security findings.",
)


@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler: log details server-side and return a generic error."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "internal error"})


def _get_or_create_metric(cls, name, *args, **kwargs):
    """Return an existing metric or create a new one, surviving reloads."""
    try:
        return cls(name, *args, **kwargs)
    except ValueError:
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

_pii_detector = PIILeakageDetector()
_rag_detector = RAGPoisoningDetector()
_emb_detector = EmbeddingSimilarityDetector()


class ScanRequest(BaseModel):
    prompt: str = Field(..., description="The user prompt sent to the LLM.")
    response: str = Field("", description="The LLM response (optional).")
    context_docs: list[str] = Field(
        default_factory=list,
        max_length=_MAX_CONTEXT_DOCS,
        description="RAG context documents injected alongside the prompt.",
    )
    session_id: str = Field("", description="Optional session identifier for canary tracking.")


class Finding(BaseModel):
    rule_id: str
    severity: str
    message: str
    detector: str
    owasp_llm_id: str = ""


class ScanResponse(BaseModel):
    scan_id: str
    findings: list[Finding]
    sarif: dict[str, Any]
    would_block: bool
    blocked: bool
    enforcement_mode: str
    duration_ms: float


def _run_detectors(req: ScanRequest) -> list[Finding]:
    """Execute synchronous detector work away from the async event loop."""
    findings: list[Finding] = []

    for r in _pii_detector.scan(req.prompt + "\n" + req.response):
        findings.append(
            Finding(
                rule_id=r["rule_id"],
                severity=r["severity"],
                message=r["message"],
                detector="pii_leakage",
                owasp_llm_id="LLM06",
            )
        )

    if req.context_docs:
        for r in _rag_detector.scan(req.prompt, req.context_docs):
            findings.append(
                Finding(
                    rule_id=r["rule_id"],
                    severity=r["severity"],
                    message=r["message"],
                    detector="rag_poisoning",
                    owasp_llm_id="LLM07",
                )
            )

    for r in _emb_detector.scan(req.prompt):
        findings.append(
            Finding(
                rule_id=r["rule_id"],
                severity=r["severity"],
                message=r["message"],
                detector="embedding_similarity",
                owasp_llm_id="LLM01",
            )
        )

    return findings


@app.get("/health")
async def health() -> JSONResponse:
    """Liveness check."""
    return JSONResponse({"status": "ok", "service": "llm-redteam-framework"})


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness fails closed until production authentication is configured."""
    if len(_API_KEY) < 32:
        raise HTTPException(status_code=503, detail="REDTEAM_API_KEY must be at least 32 characters")
    return {
        "status": "ready",
        "max_concurrent_scans": str(_MAX_CONCURRENT_SCANS),
        "scan_timeout_seconds": str(_SCAN_TIMEOUT_SECONDS),
    }


@app.get("/metrics", include_in_schema=False)
async def metrics(request: Request) -> Response:
    """Prometheus metrics endpoint; authentication is required."""
    auth_error = _check_api_key(request)
    if auth_error:
        raise HTTPException(status_code=401, detail=auth_error)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/scan", response_model=ScanResponse)
async def scan(req: ScanRequest, request: Request) -> ScanResponse:
    """Run all detectors against a prompt/response pair."""
    import uuid

    auth_error = _check_api_key(request)
    if auth_error:
        raise HTTPException(status_code=401, detail=auth_error)

    rate_key = hashlib.sha256(_API_KEY.encode("utf-8")).hexdigest()[:24]
    if _is_rate_limited(rate_key):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: max {_RATE_LIMIT} requests/minute",
        )

    if len(req.prompt) > _MAX_PROMPT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Prompt too long: {len(req.prompt)} chars exceeds max " f"{_MAX_PROMPT_LENGTH}"
            ),
        )

    total_input_chars = len(req.prompt) + len(req.response) + sum(len(doc) for doc in req.context_docs)
    if total_input_chars > _MAX_TOTAL_INPUT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Total scan input too large: {total_input_chars} chars exceeds max "
                f"{_MAX_TOTAL_INPUT_CHARS}"
            ),
        )

    t0 = time.perf_counter()
    scan_id = str(uuid.uuid4())
    all_findings: list[Finding] = []

    try:
        async with _scan_slots:
            all_findings = await asyncio.wait_for(
                run_in_threadpool(_run_detectors, req),
                timeout=_SCAN_TIMEOUT_SECONDS,
            )

        would_block = any(f.severity in ("HIGH", "CRITICAL") for f in all_findings)
        blocked = would_block and _ENFORCEMENT_MODE == "block"
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
            would_block=would_block,
            blocked=blocked,
            enforcement_mode=_ENFORCEMENT_MODE,
            duration_ms=round(duration_ms, 2),
        )

    except asyncio.TimeoutError as exc:
        SCAN_REQUESTS.labels(status="timeout").inc()
        raise HTTPException(status_code=504, detail="Scan timed out") from exc
    except Exception as exc:  # noqa: BLE001
        SCAN_REQUESTS.labels(status="error").inc()
        logger.exception("Scan error for scan_id=%s", scan_id)
        raise HTTPException(status_code=500, detail="internal error") from exc
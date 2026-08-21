"""
src/redteam/detectors/canary_tracker.py
──────────────────────────────────────────────────────────────────────────────
Canary token tracker  --  embeds unique tokens into documents and detects if
they surface in LLM outputs.

Use case
--------
You have a set of proprietary documents in your RAG corpus. You want to know:
  (a) which documents are being retrieved and passed to the LLM,
  (b) whether the LLM is leaking verbatim content from those documents.

This tracker assigns a UUID-based canary to every document at index time.
When an LLM response is checked, any canary that appears has leaked  --
confirming both retrieval and verbatim reproduction.

OWASP LLM Top 10: LLM07 (RAG Poisoning), LLM06 (Sensitive Information Disclosure)
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class CanaryRecord:
    """Metadata for a tracked canary token."""

    canary_id: str  # e.g. "CANARY-A3F1B2C4D5E6"
    doc_id: str  # caller-supplied document identifier
    doc_fingerprint: str  # SHA-256[:16] of the original document text
    inserted_at: float  # unix timestamp
    fired: bool = False  # True once detected in an LLM output
    fired_at: float = 0.0
    fired_in_session: str = ""


class CanaryTokenTracker:
    """Embed and track canary tokens across document corpora and LLM sessions.

    Parameters
    ----------
    store_path:
        Optional path to persist the canary registry as NDJSON.
        If omitted, state is in-memory only.

    Example
    -------
    >>> tracker = CanaryTokenTracker()
    >>> instrumented_doc = tracker.embed("doc-001", "Quarterly earnings: $4.2B")
    >>> # Later, after LLM generates a response:
    >>> leaks = tracker.check_response(llm_response, session_id="sess-xyz")
    >>> for canary_id, record in leaks.items():
    ...     print(f"LEAK: {canary_id} from doc {record.doc_id}")
    """

    def __init__(self, store_path: str | Path | None = None) -> None:
        self._registry: dict[str, CanaryRecord] = {}
        self._store_path = Path(store_path) if store_path else None
        if self._store_path and self._store_path.exists():
            self._load()

    # ── Embedding ─────────────────────────────────────────────────────────────

    def embed(self, doc_id: str, document_text: str) -> str:
        """Embed a unique canary into a document and register it.

        Parameters
        ----------
        doc_id:
            Caller-supplied identifier for the document (e.g. filename, chunk ID).
        document_text:
            The original document content.

        Returns
        -------
        str
            The instrumented document text with the canary appended.
            Pass this to your vector store instead of the original.
        """
        canary_id = f"CANARY-{uuid.uuid4().hex[:12].upper()}"
        doc_fingerprint = hashlib.sha256(document_text.encode()).hexdigest()[:16]

        record = CanaryRecord(
            canary_id=canary_id,
            doc_id=doc_id,
            doc_fingerprint=doc_fingerprint,
            inserted_at=time.time(),
        )
        self._registry[canary_id] = record

        if self._store_path:
            self._append_record(record)

        # Append canary as an invisible HTML comment  --  invisible to readers,
        # but present verbatim in the LLM context window.
        return f"{document_text}\n<!-- {canary_id} -->"

    def embed_batch(self, documents: dict[str, str]) -> dict[str, str]:
        """Embed canaries into a batch of documents.

        Parameters
        ----------
        documents:
            Mapping of doc_id -> document_text.

        Returns
        -------
        dict[str, str]
            Mapping of doc_id -> instrumented_text.
        """
        return {doc_id: self.embed(doc_id, text) for doc_id, text in documents.items()}

    # ── Detection ─────────────────────────────────────────────────────────────

    def check_response(
        self,
        response_text: str,
        session_id: str = "",
    ) -> dict[str, CanaryRecord]:
        """Scan an LLM response for canary tokens.

        Parameters
        ----------
        response_text:
            The LLM-generated text to inspect.
        session_id:
            Optional identifier for the conversation/request session.

        Returns
        -------
        dict[str, CanaryRecord]
            Mapping of canary_id -> CanaryRecord for every canary that fired.
            Empty dict if no canaries leaked.
        """
        fired: dict[str, CanaryRecord] = {}
        for canary_id, record in self._registry.items():
            if canary_id in response_text:
                record.fired = True
                record.fired_at = time.time()
                record.fired_in_session = session_id
                fired[canary_id] = record
                if self._store_path:
                    self._append_record(record)
        return fired

    def findings_from_leaks(
        self,
        fired: dict[str, CanaryRecord],
    ) -> list[dict[str, Any]]:
        """Convert fired canaries to standard finding dicts."""
        findings: list[dict[str, Any]] = []
        for canary_id, record in fired.items():
            findings.append(
                {
                    "rule_id": "LLM07-CanaryFired",
                    "severity": "HIGH",
                    "message": (
                        f"Canary token {canary_id!r} embedded in document {record.doc_id!r} "
                        f"(fingerprint={record.doc_fingerprint}) appeared verbatim in LLM output. "
                        f"Session: {record.fired_in_session or 'unknown'}."
                    ),
                    "detector": "canary_tracker",
                    "owasp_llm_id": "LLM07",
                }
            )
        return findings

    # ── Registry access ────────────────────────────────────────────────────────

    def registry_summary(self) -> dict[str, Any]:
        """Return a summary of tracked canaries."""
        total = len(self._registry)
        fired = sum(1 for r in self._registry.values() if r.fired)
        return {
            "total_canaries": total,
            "fired": fired,
            "unfired": total - fired,
            "fire_rate": fired / total if total else 0.0,
        }

    # ── Persistence helpers ───────────────────────────────────────────────────

    def _append_record(self, record: CanaryRecord) -> None:
        assert self._store_path is not None
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        with self._store_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record)) + "\n")

    def _load(self) -> None:
        assert self._store_path is not None
        with self._store_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    record = CanaryRecord(**data)
                    self._registry[record.canary_id] = record

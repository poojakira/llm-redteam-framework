"""
src/redteam/detectors/__init__.py
──────────────────────────────────────────────────────────────────────────────
Public API for the detectors sub-package.

Exports
-------
RAGPoisoningDetector       --  LLM04/LLM02 poisoned-context + canary-leak signals
PIILeakageDetector         --  LLM02  regex + entropy + spaCy NER
CanaryTokenTracker         --  LLM02  per-document canary embed/fire tracking
EmbeddingSimilarityDetector  --  LLM01  cosine similarity vs seed attack corpus
ToolPermissionBoundaryDetector -- LLM06 deterministic least-privilege tool boundary
"""

from __future__ import annotations

from redteam.detectors.canary_tracker import CanaryTokenTracker
from redteam.detectors.embedding_similarity import EmbeddingSimilarityDetector
from redteam.detectors.pii_leakage import PIILeakageDetector
from redteam.detectors.rag_poisoning import RAGPoisoningDetector
from redteam.detectors.tool_permissions import ToolPermissionBoundaryDetector

__all__ = [
    "RAGPoisoningDetector",
    "PIILeakageDetector",
    "CanaryTokenTracker",
    "EmbeddingSimilarityDetector",
    "ToolPermissionBoundaryDetector",
]

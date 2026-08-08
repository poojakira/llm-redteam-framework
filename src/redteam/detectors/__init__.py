"""
src/redteam/detectors/__init__.py
──────────────────────────────────────────────────────────────────────────────
Public API for the detectors sub-package.

Exports
-------
RAGPoisoningDetector      — LLM07  canary injection + injection pattern scan
PIILeakageDetector        — LLM06  regex + entropy + spaCy NER
CanaryTokenTracker        — LLM07  per-document canary embed/fire tracking
EmbeddingSimilarityDetector — LLM01  cosine similarity vs seed attack corpus
"""

from __future__ import annotations

from redteam.detectors.canary_tracker import CanaryTokenTracker
from redteam.detectors.embedding_similarity import EmbeddingSimilarityDetector
from redteam.detectors.pii_leakage import PIILeakageDetector
from redteam.detectors.rag_poisoning import RAGPoisoningDetector

__all__ = [
    "RAGPoisoningDetector",
    "PIILeakageDetector",
    "CanaryTokenTracker",
    "EmbeddingSimilarityDetector",
]

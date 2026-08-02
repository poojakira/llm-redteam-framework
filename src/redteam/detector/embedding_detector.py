"""Embedding-based adversarial prompt detector.

Uses sentence-transformers to encode prompts into dense vectors,
then classifies using a trained logistic regression on the embedding space.
This catches semantic paraphrases that character n-gram models miss.

Requires: pip install sentence-transformers
Fallback: uses TF-IDF detector if sentence-transformers unavailable.
"""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)

# Lazy-loaded optional dependency.
_SENTENCE_TRANSFORMERS_AVAILABLE: bool | None = None
_SentenceTransformer = None


def _check_sentence_transformers() -> bool:
    """Check if sentence-transformers is installed (cached)."""
    global _SENTENCE_TRANSFORMERS_AVAILABLE, _SentenceTransformer
    if _SENTENCE_TRANSFORMERS_AVAILABLE is None:
        try:
            from sentence_transformers import SentenceTransformer

            _SentenceTransformer = SentenceTransformer
            _SENTENCE_TRANSFORMERS_AVAILABLE = True
        except ImportError:
            _SENTENCE_TRANSFORMERS_AVAILABLE = False
    return _SENTENCE_TRANSFORMERS_AVAILABLE


class EmbeddingDetector:
    """Dense-embedding based adversarial prompt classifier.

    Uses all-MiniLM-L6-v2 (384-d) embeddings + logistic regression.
    Falls back to raising ImportError if sentence-transformers is missing.

    Label convention: ``1`` = adversarial, ``0`` = benign.
    """

    DEFAULT_MODEL_NAME: str = "all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        C: float = 4.0,  # noqa: N803
        max_iter: int = 2000,
        random_state: int = 42,
    ) -> None:
        if not _check_sentence_transformers():
            raise ImportError(
                "sentence-transformers is required for EmbeddingDetector. "
                "Install with: pip install sentence-transformers"
            )
        self.model_name = model_name
        self._encoder = _SentenceTransformer(model_name)
        self._classifier = LogisticRegression(
            C=C,
            max_iter=max_iter,
            class_weight="balanced",
            random_state=random_state,
        )
        self._fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        """Whether :meth:`train` has been called successfully."""
        return self._fitted

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        """Encode texts to dense vectors using the sentence transformer."""
        return self._encoder.encode(
            list(texts),
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def train(self, texts: Sequence[str], labels: Sequence[int]) -> "EmbeddingDetector":
        """Fit the detector on labelled prompts.

        Parameters
        ----------
        texts:
            Prompt strings.
        labels:
            Matching binary labels (``1`` adversarial, ``0`` benign).
        """
        if len(texts) != len(labels):
            raise ValueError("texts and labels must have equal length")
        if len(texts) == 0:
            raise ValueError("cannot train on an empty dataset")

        embeddings = self._encode(texts)
        self._classifier.fit(embeddings, np.asarray(labels, dtype=int))
        self._fitted = True
        return self

    def _check_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError("detector is not trained; call train() first")

    def predict(self, texts: Sequence[str]) -> np.ndarray:
        """Return hard 0/1 predictions for ``texts``."""
        self._check_fitted()
        embeddings = self._encode(texts)
        return self._classifier.predict(embeddings)

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        """Return P(adversarial) for each text as a 1-D float array."""
        self._check_fitted()
        embeddings = self._encode(texts)
        return self._classifier.predict_proba(embeddings)[:, 1]


def get_detector(prefer_embedding: bool = True, **kwargs):
    """Factory that returns the best available detector.

    Parameters
    ----------
    prefer_embedding:
        If True and sentence-transformers is available, returns
        :class:`EmbeddingDetector`. Otherwise falls back to
        :class:`~redteam.detector.RedTeamDetector`.
    **kwargs:
        Passed to the detector constructor.

    Returns
    -------
    EmbeddingDetector or RedTeamDetector
    """
    if prefer_embedding and _check_sentence_transformers():
        logger.info("Using EmbeddingDetector (sentence-transformers available)")
        return EmbeddingDetector(**kwargs)
    else:
        from .detector import DetectorConfig, RedTeamDetector

        logger.info("Falling back to TF-IDF RedTeamDetector")
        config_kwargs = {}
        if "random_state" in kwargs:
            config_kwargs["random_state"] = kwargs["random_state"]
        if "C" in kwargs:
            config_kwargs["C"] = kwargs["C"]
        return RedTeamDetector(config=DetectorConfig(**config_kwargs))

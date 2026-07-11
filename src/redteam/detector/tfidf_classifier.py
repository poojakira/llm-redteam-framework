"""Offline TF-IDF + logistic-regression adversarial-prompt detector.

Why TF-IDF and not a neural classifier for *this* job:

- **Offline & tiny.** No model download, no GPU, no network. It trains in milliseconds
  and ships as a small pickle -- ideal for a CI gate or a local pre-filter.
- **Fast.** Scoring is a sparse dot product; you can screen millions of prompts.
- **Interpretable.** Coefficients map directly to tokens, so you can see *which* words
  ("ignore", "override", "DAN") drive a flag. A transformer's decision is opaque.

The trade-off is that TF-IDF keys on surface tokens, so it is strongest against the
lexical tells of known jailbreak families and weakest against paraphrase. That is the
correct tool here: a cheap, transparent first line that catches the bulk of known
patterns, not a claim of semantic robustness.
"""

from __future__ import annotations

import pickle
from collections.abc import Sequence
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score


class AdversarialDetector:
    """Binary detector: 1 = adversarial prompt, 0 = benign prompt."""

    def __init__(self, max_features: int = 5000) -> None:
        self.max_features = int(max_features)
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=(1, 2),
            lowercase=True,
            sublinear_tf=True,
        )
        self.classifier = LogisticRegression(max_iter=1000, class_weight="balanced")
        self._fitted = False

    def train(self, texts: Sequence[str], labels: Sequence[int]) -> None:
        """Fit the vectorizer and classifier. ``labels``: 1 adversarial, 0 benign."""
        features = self.vectorizer.fit_transform(list(texts))
        self.classifier.fit(features, list(labels))
        self._fitted = True

    def _check_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError("Detector is not trained. Call train() first.")

    def predict(self, texts: Sequence[str]) -> list[int]:
        """Return hard 0/1 labels for each text."""
        self._check_fitted()
        features = self.vectorizer.transform(list(texts))
        return [int(p) for p in self.classifier.predict(features)]

    def predict_proba(self, texts: Sequence[str]) -> list[float]:
        """Return P(adversarial) for each text."""
        self._check_fitted()
        features = self.vectorizer.transform(list(texts))
        return [float(p) for p in self.classifier.predict_proba(features)[:, 1]]

    def auc(self, texts: Sequence[str], labels: Sequence[int]) -> float:
        """ROC-AUC on a labelled set (must exceed 0.85 on the synthetic test split)."""
        scores = self.predict_proba(texts)
        return float(roc_auc_score(list(labels), scores))

    def save(self, path: str) -> None:
        """Persist the fitted vectorizer + classifier via pickle."""
        self._check_fitted()
        payload = {
            "max_features": self.max_features,
            "vectorizer": self.vectorizer,
            "classifier": self.classifier,
        }
        Path(path).write_bytes(pickle.dumps(payload))

    @classmethod
    def load(cls, path: str) -> "AdversarialDetector":
        """Load a detector previously written by :meth:`save`."""
        payload = pickle.loads(Path(path).read_bytes())
        detector = cls(max_features=payload["max_features"])
        detector.vectorizer = payload["vectorizer"]
        detector.classifier = payload["classifier"]
        detector._fitted = True
        return detector

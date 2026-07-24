"""TF-IDF (character n-gram) + LogisticRegression adversarial-prompt detector."""

from __future__ import annotations

import hashlib
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


@dataclass
class DetectorConfig:
    """Hyper-parameters for :class:`RedTeamDetector`.

    Character n-grams (``analyzer="char_wb"``) are used deliberately: they are
    robust to the spacing / leetspeak / delimiter obfuscations produced by the
    generators, which token-level features tend to miss.
    """

    ngram_range: tuple[int, int] = (2, 5)
    min_df: int = 1
    sublinear_tf: bool = True
    C: float = 4.0
    max_iter: int = 2000
    class_weight: str | None = "balanced"
    random_state: int = 42

    def build_pipeline(self) -> Pipeline:
        """Construct the (vectorizer -> classifier) sklearn pipeline."""
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=self.ngram_range,
            min_df=self.min_df,
            sublinear_tf=self.sublinear_tf,
            lowercase=True,
        )
        classifier = LogisticRegression(
            C=self.C,
            max_iter=self.max_iter,
            class_weight=self.class_weight,
            random_state=self.random_state,
        )
        return Pipeline([("tfidf", vectorizer), ("clf", classifier)])


class RedTeamDetector:
    """A binary classifier that flags adversarial prompts.

    Label convention: ``1`` = adversarial, ``0`` = benign.
    """

    def __init__(self, config: DetectorConfig | None = None) -> None:
        self.config: DetectorConfig = config or DetectorConfig()
        self.pipeline: Pipeline = self.config.build_pipeline()
        self._fitted: bool = False

    @property
    def is_fitted(self) -> bool:
        """Whether :meth:`train` has been called successfully."""
        return self._fitted

    def train(self, texts: Sequence[str], labels: Sequence[int]) -> "RedTeamDetector":
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
        self.pipeline.fit(list(texts), np.asarray(labels, dtype=int))
        self._fitted = True
        return self

    def _check_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError("detector is not trained; call train() first")

    def predict(self, texts: Sequence[str]) -> np.ndarray:
        """Return hard 0/1 predictions for ``texts``."""
        self._check_fitted()
        return self.pipeline.predict(list(texts))

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        """Return P(adversarial) for each text as a 1-D float array."""
        self._check_fitted()
        return self.pipeline.predict_proba(list(texts))[:, 1]

    def _sha256(self, data: bytes) -> str:
        """Return SHA-256 hex digest of ``data``."""
        return hashlib.sha256(data).hexdigest()

    def save(self, path: str | Path) -> None:
        """Persist the fitted detector to ``path`` with SHA-256 integrity checksum.

        Writes two files:
        - ``path``: pickle-serialized model
        - ``path + ".sha256"``: SHA-256 hex digest of the pickle bytes

        Raises:
            RuntimeError: if detector is not fitted.
        """
        self._check_fitted()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {"config": self.config, "pipeline": self.pipeline}
        data = pickle.dumps(payload)
        checksum = hashlib.sha256(data).hexdigest()

        path.write_bytes(data)
        (path.parent / (path.name + ".sha256")).write_text(checksum)

    @classmethod
    def load(cls, path: str | Path, *, trusted: bool = False) -> "RedTeamDetector":
        """Load a detector previously written by :meth:`save`.

        Security: refuses to load if the SHA-256 checksum file is missing or
        the checksum doesn't match, preventing arbitrary code execution via
        tampered pickle files.

        Args:
            path: Path to the pickle file.
            trusted: If True, skip integrity check (for trusted sources only).
                     Default False for safety.

        Raises:
            ValueError: if integrity check fails and ``trusted=False``.
            FileNotFoundError: if model or checksum file is missing.
            RuntimeError: if loaded payload is malformed.
        """
        path = Path(path)
        checksum_path = path.parent / (path.name + ".sha256")

        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        if not checksum_path.exists():
            raise FileNotFoundError(
                f"Integrity checksum file not found: {checksum_path}. "
                "Model may have been saved without integrity protection or "
                "the checksum file was removed. Refusing to load."
            )

        data = path.read_bytes()
        expected = path.parent.joinpath(path.name + ".sha256").read_text().strip()
        actual = hashlib.sha256(path.read_bytes()).hexdigest()

        if not trusted and actual != expected:
            raise ValueError(
                "Integrity check failed: model file checksum mismatch. "
                "File may have been tampered with. Use trusted=True only if "
                "you are certain the file is safe."
            )

        payload = pickle.loads(path.read_bytes())
        if not isinstance(payload, dict) or "config" not in payload or "pipeline" not in payload:
            raise RuntimeError("Malformed model payload: expected dict with 'config' and 'pipeline'")

        detector = cls(config=payload["config"])
        detector.pipeline = payload["pipeline"]
        detector._fitted = True
        return detector
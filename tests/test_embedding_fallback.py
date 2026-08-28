"""Tests for embedding detector import-guard / graceful degradation.

We do NOT install sentence-transformers. We exercise:
  - the ImportError fallback in _check_sentence_transformers (real, uncached)
  - EmbeddingDetector constructor raising ImportError when unavailable
  - get_detector falling back to RedTeamDetector
  - the "available" branch by monkeypatching the module cache + a fake encoder
"""

from __future__ import annotations

import sys

sys.path.insert(0, "src")

import numpy as np
import pytest

import redteam.detector.embedding_detector as ed
from redteam.detector.detector import RedTeamDetector


def _reset_cache():
    ed._SENTENCE_TRANSFORMERS_AVAILABLE = None
    ed._SentenceTransformer = None


def test_check_sentence_transformers_returns_false_when_absent():
    _reset_cache()
    # sentence-transformers is not installed in this env
    assert ed._check_sentence_transformers() is False
    # cached now
    assert ed._SENTENCE_TRANSFORMERS_AVAILABLE is False


def test_constructor_raises_importerror_without_dependency():
    _reset_cache()
    with pytest.raises(ImportError, match="sentence-transformers"):
        ed.EmbeddingDetector()


def test_get_detector_falls_back_to_redteam_detector():
    _reset_cache()
    det = ed.get_detector(prefer_embedding=True)
    assert isinstance(det, RedTeamDetector)


def test_get_detector_passes_config_kwargs():
    _reset_cache()
    det = ed.get_detector(prefer_embedding=True, random_state=7, C=2.0)
    assert isinstance(det, RedTeamDetector)
    assert det.config.random_state == 7
    assert det.config.C == 2.0


def test_get_detector_prefer_embedding_false():
    _reset_cache()
    det = ed.get_detector(prefer_embedding=False)
    assert isinstance(det, RedTeamDetector)


class _FakeEncoder:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, texts, **kwargs):
        # deterministic 2-d embedding based on text length parity
        return np.array([[len(t) % 2, (len(t) + 1) % 2] for t in texts], dtype=float)


def test_available_branch_train_predict(monkeypatch):
    """Force the 'available' path with a fake SentenceTransformer to cover
    train/predict/predict_proba/_encode and is_fitted."""
    monkeypatch.setattr(ed, "_SENTENCE_TRANSFORMERS_AVAILABLE", True)
    monkeypatch.setattr(ed, "_SentenceTransformer", _FakeEncoder)

    det = ed.EmbeddingDetector(model_name="fake-model")
    assert det.is_fitted is False
    assert det.model_name == "fake-model"

    texts = ["adversarial one", "benign", "attack here", "hi"]
    labels = [1, 0, 1, 0]
    ret = det.train(texts, labels)
    assert ret is det
    assert det.is_fitted is True

    preds = det.predict(["some text", "x"])
    assert len(preds) == 2
    assert set(np.unique(preds)).issubset({0, 1})

    proba = det.predict_proba(["some text", "x"])
    assert proba.shape == (2,)
    assert np.all((proba >= 0) & (proba <= 1))


def test_train_length_mismatch(monkeypatch):
    monkeypatch.setattr(ed, "_SENTENCE_TRANSFORMERS_AVAILABLE", True)
    monkeypatch.setattr(ed, "_SentenceTransformer", _FakeEncoder)
    det = ed.EmbeddingDetector()
    with pytest.raises(ValueError, match="equal length"):
        det.train(["a", "b"], [1])


def test_train_empty_dataset(monkeypatch):
    monkeypatch.setattr(ed, "_SENTENCE_TRANSFORMERS_AVAILABLE", True)
    monkeypatch.setattr(ed, "_SentenceTransformer", _FakeEncoder)
    det = ed.EmbeddingDetector()
    with pytest.raises(ValueError, match="empty dataset"):
        det.train([], [])


def test_predict_before_train_raises(monkeypatch):
    monkeypatch.setattr(ed, "_SENTENCE_TRANSFORMERS_AVAILABLE", True)
    monkeypatch.setattr(ed, "_SentenceTransformer", _FakeEncoder)
    det = ed.EmbeddingDetector()
    with pytest.raises(RuntimeError, match="not trained"):
        det.predict(["x"])
    with pytest.raises(RuntimeError, match="not trained"):
        det.predict_proba(["x"])


def test_get_detector_returns_embedding_when_available(monkeypatch):
    monkeypatch.setattr(ed, "_SENTENCE_TRANSFORMERS_AVAILABLE", True)
    monkeypatch.setattr(ed, "_SentenceTransformer", _FakeEncoder)
    det = ed.get_detector(prefer_embedding=True, model_name="fake-model")
    assert isinstance(det, ed.EmbeddingDetector)


def teardown_module(module):
    _reset_cache()

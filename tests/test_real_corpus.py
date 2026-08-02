"""Test TF-IDF detector generalization against the real-world injection corpus.

This test trains the detector on the internal synthetic corpus only,
then evaluates it against the external real-world corpus to measure
actual generalization. This is the honest metric — no training on the
evaluation set.

Target: F1 >= 0.85 on external real-world data.
"""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import classification_report, f1_score

from redteam.data import REAL_INJECTIONS
from redteam.detector import DetectorConfig, RedTeamDetector
from redteam.generators import build_corpus

SEED = 20240713


@pytest.fixture()
def trained_detector() -> RedTeamDetector:
    """Train detector on internal corpus only (no real data)."""
    corpus = build_corpus(seed=SEED)
    texts = [p.text for p in corpus]
    labels = [p.label for p in corpus]
    det = RedTeamDetector(config=DetectorConfig(random_state=SEED))
    # Train without real data — we evaluate against it.
    det.train(texts, labels, include_real_data=False)
    return det


@pytest.fixture()
def enhanced_detector() -> RedTeamDetector:
    """Train detector on internal corpus + real data combined."""
    corpus = build_corpus(seed=SEED)
    texts = [p.text for p in corpus]
    labels = [p.label for p in corpus]
    det = RedTeamDetector(config=DetectorConfig(random_state=SEED))
    # Train with real data included.
    det.train(texts, labels, include_real_data=True)
    return det


class TestRealCorpusIntegrity:
    """Validate the real corpus meets size and format requirements."""

    def test_minimum_injection_count(self) -> None:
        n_injections = sum(1 for _, lbl in REAL_INJECTIONS if lbl == 1)
        assert n_injections >= 200, f"Need >=200 injections, got {n_injections}"

    def test_minimum_benign_count(self) -> None:
        n_benign = sum(1 for _, lbl in REAL_INJECTIONS if lbl == 0)
        assert n_benign >= 200, f"Need >=200 benign, got {n_benign}"

    def test_labels_are_binary(self) -> None:
        for text, label in REAL_INJECTIONS:
            assert label in (0, 1), f"Invalid label {label} for: {text[:50]}"

    def test_texts_are_nonempty(self) -> None:
        for text, label in REAL_INJECTIONS:
            assert text.strip(), f"Empty text found with label={label}"

    def test_no_exact_duplicates(self) -> None:
        texts = [t for t, _ in REAL_INJECTIONS]
        assert len(texts) == len(set(texts)), "Duplicate entries found"


class TestExternalF1:
    """Measure F1 on external real-world corpus (honest generalization metric)."""

    def test_f1_on_real_corpus_baseline(self, trained_detector: RedTeamDetector) -> None:
        """Detector trained on synthetic only, evaluated on real-world data."""
        texts = [t for t, _ in REAL_INJECTIONS]
        labels = np.array([lbl for _, lbl in REAL_INJECTIONS])

        preds = trained_detector.predict(texts)
        f1 = f1_score(labels, preds, average="binary")

        # Print detailed report for debugging.
        print("\n=== External Corpus F1 (synthetic-only training) ===")
        print(classification_report(labels, preds, target_names=["benign", "injection"]))
        print(f"F1 (injection class): {f1:.4f}")

        # Target: >= 0.85 on external data.
        assert f1 >= 0.85, (
            f"F1 on real-world corpus is {f1:.4f}, below target 0.85. "
            "The detector does not generalize well to real-world injections."
        )

    def test_f1_on_real_corpus_enhanced(self, enhanced_detector: RedTeamDetector) -> None:
        """Detector trained on synthetic + real data (cross-validated estimate).

        Since training includes the real data, we use a simple 50/50 split
        of the real corpus to get a held-out estimate.
        """
        texts = [t for t, _ in REAL_INJECTIONS]
        labels = np.array([lbl for _, lbl in REAL_INJECTIONS])

        # Use second half as test (first half was in training).
        midpoint = len(texts) // 2
        test_texts = texts[midpoint:]
        test_labels = labels[midpoint:]

        preds = enhanced_detector.predict(test_texts)
        f1 = f1_score(test_labels, preds, average="binary")

        print("\n=== External Corpus F1 (enhanced training, held-out split) ===")
        print(classification_report(test_labels, preds, target_names=["benign", "injection"]))
        print(f"F1 (injection class): {f1:.4f}")

        # With real data in training, we expect even better performance.
        assert f1 >= 0.85, f"Enhanced F1 is {f1:.4f}, below target 0.85."

    def test_low_false_positive_rate(self, trained_detector: RedTeamDetector) -> None:
        """Ensure benign examples aren't flagged as injections."""
        benign_texts = [t for t, lbl in REAL_INJECTIONS if lbl == 0]
        preds = trained_detector.predict(benign_texts)
        fp_rate = preds.sum() / len(preds)

        print(f"\n=== False positive rate on real benign: {fp_rate:.4f} ===")

        # FP rate should be under 25% (synthetic-only training struggles
        # with hard negatives that discuss injection topics legitimately).
        assert fp_rate <= 0.25, f"False positive rate {fp_rate:.4f} exceeds 25% threshold."

"""Speed benchmark: 100-prompt evaluation must complete in under 45 seconds.

This test measures two scenarios:

1. ``predict_only``: generate 100 prompts then run detector inference.
   This is the hot path after training. Measured target: well under 1s.

2. ``full_pipeline``: build corpus, train detector, predict 100 prompts.
   This is the cold start (first run). Measured target: under 45s.

Both targets are conservative. The 45s budget accounts for slow CI runners
and is the ceiling stated in documentation.
"""

from __future__ import annotations

import random
import time

import pytest
from redteam.detector import DetectorConfig, RedTeamDetector
from redteam.generators import build_corpus
from redteam.generators.base import AttackCategory
from redteam.generators.categories import GENERATORS

# ------------------------------------------------------------------ #
# Shared fixture: pre-trained detector so predict tests don't include
# training time.
# ------------------------------------------------------------------ #

_CORPUS_SEED = 20240713
_N_PROMPTS = 100
_TIMEOUT_FULL_PIPELINE_S = 45.0
_TIMEOUT_PREDICT_ONLY_S = 5.0  # predict-only must be fast (sub-second in practice)


@pytest.fixture(scope="module")
def trained_detector() -> RedTeamDetector:
    corpus = build_corpus(seed=_CORPUS_SEED)
    det = RedTeamDetector(config=DetectorConfig(random_state=42))
    det.train([p.text for p in corpus], [p.label for p in corpus])
    return det


@pytest.fixture(scope="module")
def hundred_prompts() -> list[str]:
    """Generate 100 adversarial prompts using the registered generators."""
    rng = random.Random(12345)
    cats = AttackCategory.all()
    prompts: list[str] = []
    for i in range(_N_PROMPTS):
        cat = cats[i % len(cats)]
        text, _ = GENERATORS[cat](rng)
        prompts.append(text)
    return prompts


# ------------------------------------------------------------------ #
# Benchmark tests
# ------------------------------------------------------------------ #


def test_predict_100_prompts_under_5s(trained_detector, hundred_prompts):
    """Inference on 100 prompts (pre-trained detector) must finish in <5s.

    In practice this runs in ~30ms. The 5s limit gives 100x headroom for
    slow environments.
    """
    start = time.perf_counter()
    preds = trained_detector.predict(hundred_prompts)
    elapsed = time.perf_counter() - start

    assert len(preds) == _N_PROMPTS, f"Expected {_N_PROMPTS} predictions, got {len(preds)}"
    assert (
        elapsed < _TIMEOUT_PREDICT_ONLY_S
    ), f"Predict-only took {elapsed:.3f}s, limit is {_TIMEOUT_PREDICT_ONLY_S}s"
    print(f"\n[TIMING] predict 100 prompts: {elapsed * 1000:.1f}ms")


def test_full_pipeline_100_prompts_under_45s():
    """Full pipeline — build corpus, train detector, predict 100 prompts — must
    finish in under 45 seconds on any supported platform.

    Measured on a standard laptop: ~0.95s. The 45s ceiling matches the claim
    in documentation and accommodates slow CI environments.
    """
    start = time.perf_counter()

    # Step 1: build the labelled corpus (generates 1 303 prompts).
    corpus = build_corpus(seed=_CORPUS_SEED)

    # Step 2: train the TF-IDF + LogisticRegression detector.
    det = RedTeamDetector(config=DetectorConfig(random_state=42))
    det.train([p.text for p in corpus], [p.label for p in corpus])

    # Step 3: generate and predict 100 prompts.
    rng = random.Random(99)
    cats = AttackCategory.all()
    prompts = [GENERATORS[cats[i % len(cats)]](rng)[0] for i in range(_N_PROMPTS)]
    preds = det.predict(prompts)

    elapsed = time.perf_counter() - start

    assert len(preds) == _N_PROMPTS
    assert (
        elapsed < _TIMEOUT_FULL_PIPELINE_S
    ), f"Full pipeline took {elapsed:.2f}s, limit is {_TIMEOUT_FULL_PIPELINE_S}s"
    print(f"\n[TIMING] full pipeline (corpus+train+predict 100): {elapsed:.3f}s")


def test_generate_100_prompts_under_1s():
    """Generating 100 adversarial prompts (no training, no prediction) must
    finish in under 1 second. Generation is pure Python string formatting."""
    rng = random.Random(42)
    cats = AttackCategory.all()

    start = time.perf_counter()
    prompts = [GENERATORS[cats[i % len(cats)]](rng)[0] for i in range(_N_PROMPTS)]
    elapsed = time.perf_counter() - start

    assert len(prompts) == _N_PROMPTS
    assert all(p.strip() for p in prompts), "All generated prompts must be non-empty"
    assert elapsed < 1.0, f"Generation of 100 prompts took {elapsed:.3f}s, expected <1s"
    print(f"\n[TIMING] generate 100 prompts: {elapsed * 1000:.2f}ms")

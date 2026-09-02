"""Pin the OOD (novel-phrasing) benchmark result.

This test enforces the honest headline of the framework: the character n-gram
detector loses material performance on natural-language paraphrases that lack
the structural tells present in the training templates. It guards against two
kinds of silent drift:

* The OOD F1 quietly climbing toward the in-distribution number (which would
  mean the "novel" fixtures leaked structural markers and the benchmark stopped
  being a fair OOD test).
* The OOD F1 collapsing far below the documented figure (a regression).

The measured value at pinning time is F1 = 0.83 (precision 0.79, recall 0.88),
a material drop from the grouped-split F1 of 0.97.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_BENCH = Path(__file__).resolve().parent.parent / "benchmarks" / "ood_novel_phrasings.py"
_spec = importlib.util.spec_from_file_location("ood_novel_phrasings", _BENCH)
assert _spec is not None and _spec.loader is not None
ood = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ood)


def test_ood_benchmark_is_deterministic_and_degraded() -> None:
    report = ood.run_ood_benchmark()

    # Balanced fixture set.
    assert report["n_adversarial"] == 25
    assert report["n_benign"] == 25

    # The OOD F1 must be materially below the in-distribution grouped-split F1
    # (0.97): this degradation is the framework's central, honest finding.
    assert report["f1_score"] < 0.90, "OOD fixtures no longer look out-of-distribution"

    # It must not have collapsed either — that would be a real regression.
    assert report["f1_score"] > 0.70

    # Pin the exact deterministic value measured at authoring time.
    assert report["f1_score"] == 0.8302
    assert report["precision"] == 0.7857
    assert report["recall"] == 0.88


def test_ood_gap_from_grouped_split_is_real() -> None:
    report = ood.run_ood_benchmark()
    grouped_f1 = report["reference_grouped_f1"]
    # At least a 10-point F1 drop from in-distribution to novel phrasings.
    assert grouped_f1 - report["f1_score"] >= 0.10

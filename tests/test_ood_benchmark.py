"""Methodology guards for the OOD novel-phrasing benchmark."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_BENCH = Path(__file__).resolve().parent.parent / "benchmarks" / "ood_novel_phrasings.py"
_spec = importlib.util.spec_from_file_location("ood_novel_phrasings", _BENCH)
assert _spec is not None and _spec.loader is not None
ood = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ood)


def test_ood_benchmark_uses_comparable_training_and_has_no_exact_overlap() -> None:
    report = ood.run_ood_benchmark()

    assert report["methodology"].startswith("same grouped-split detector")
    assert report["corpus_seed"] == 20240713
    assert report["split_seed"] == 42
    assert report["n_adversarial"] == 25
    assert report["n_benign"] == 25
    assert report["exact_training_fixture_overlap"] == 0
    assert report["overlap_examples"] == []


def test_ood_metrics_are_valid_and_show_the_measured_gap() -> None:
    report = ood.run_ood_benchmark()

    for key in ("precision", "recall", "f1_score", "accuracy", "reference_grouped_f1"):
        assert 0.0 <= report[key] <= 1.0

    # OOD should remain harder than the grouped synthetic holdout. Do not pin an
    # old exact value produced by a different training configuration.
    assert report["f1_score"] < report["reference_grouped_f1"]

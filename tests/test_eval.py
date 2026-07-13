"""Seed-pinned tests for the held-out evaluation harness.

These lock the headline metrics reported in the README so CI can re-verify
them. If the generators, detector, or split logic change, these assertions must
be updated to the new *measured* values -- never hand-edited to a wished-for
number.
"""

from __future__ import annotations

import pytest

from redteam.eval import evaluate
from redteam.eval.harness import _grouped_split, _template_prefix
from redteam.generators import build_corpus


def test_grouped_split_headline_metrics() -> None:
    report, _ = evaluate(split_mode="grouped", test_size=0.3, seed=42)
    assert report.split_mode == "grouped"
    # Structural counts (exact).
    assert report.n_total == 1303
    assert report.n_test == 414
    assert report.n_test_adversarial == 238
    assert report.n_test_benign == 176
    assert report.n_test_templates == 26
    assert report.false_negatives == 0
    assert report.false_positives == 14
    # Measured metrics (pinned to the values produced by this seed).
    assert report.precision == pytest.approx(0.9444444, abs=1e-6)
    assert report.recall == pytest.approx(1.0, abs=1e-6)
    assert report.f1 == pytest.approx(0.9714286, abs=1e-6)
    assert report.false_positive_rate == pytest.approx(0.0795455, abs=1e-6)
    assert report.accuracy == pytest.approx(0.9661836, abs=1e-6)


def test_random_split_is_optimistic() -> None:
    report, _ = evaluate(split_mode="random", test_size=0.3, seed=42)
    assert report.f1 == pytest.approx(1.0, abs=1e-6)
    assert report.false_positive_rate == pytest.approx(0.0, abs=1e-6)


def test_evaluate_is_deterministic() -> None:
    r1, _ = evaluate(split_mode="grouped", seed=42)
    r2, _ = evaluate(split_mode="grouped", seed=42)
    assert r1.to_dict() == r2.to_dict()


def test_grouped_split_holds_out_templates() -> None:
    corpus = build_corpus()
    train, test = _grouped_split(corpus, test_size=0.3, seed=42)
    train_templates = {p.template_id for p in train}
    test_templates = {p.template_id for p in test}
    # Test templates are unseen during training (true held-out generalization).
    assert train_templates.isdisjoint(test_templates)
    # Both splits are non-empty and cover both classes.
    assert train and test
    assert {p.label for p in train} == {0, 1}
    assert {p.label for p in test} == {0, 1}


def test_grouped_split_covers_every_category() -> None:
    corpus = build_corpus()
    train, test = _grouped_split(corpus, test_size=0.3, seed=42)
    train_prefixes = {_template_prefix(p.template_id) for p in train}
    test_prefixes = {_template_prefix(p.template_id) for p in test}
    for cat in ("direct_override", "role_switch", "context_escape",
                "indirect_embed", "obfuscation", "multi_step"):
        assert cat in train_prefixes
        assert cat in test_prefixes


def test_reported_fp_rate_is_nonzero() -> None:
    """The hard negatives must actually cost the detector some false positives."""
    report, _ = evaluate(split_mode="grouped", seed=42)
    assert report.false_positive_rate > 0.0

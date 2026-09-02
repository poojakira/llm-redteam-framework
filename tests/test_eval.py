"""Seed-pinned tests for the held-out evaluation harness.

These lock the headline metrics reported in the README so CI can re-verify
them. If the generators, detector, or split logic change, these assertions must
be updated to the new *measured* values -- never hand-edited to a wished-for
number.
"""

from __future__ import annotations

import pytest

from redteam.eval import evaluate
from redteam.eval.harness import (
    _grouped_split,
    _template_prefix,
    evaluate_with_holdout,
    grouped_train_test_split,
)
from redteam.generators import LABEL_ADVERSARIAL, LABEL_BENIGN, build_corpus


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
    for cat in (
        "direct_override",
        "role_switch",
        "context_escape",
        "indirect_embed",
        "obfuscation",
        "multi_step",
    ):
        assert cat in train_prefixes
        assert cat in test_prefixes


def test_reported_fp_rate_is_nonzero() -> None:
    """The hard negatives must actually cost the detector some false positives."""
    report, _ = evaluate(split_mode="grouped", seed=42)
    assert report.false_positive_rate > 0.0


# ---------------------------------------------------------------------------
# New tests for grouped_train_test_split and evaluate_with_holdout
# ---------------------------------------------------------------------------


def test_grouped_split_no_template_overlap() -> None:
    """No template_id should appear in both the train and test splits."""
    corpus = build_corpus()
    texts = [p.text for p in corpus]
    labels = [p.label for p in corpus]
    template_ids = [p.template_id for p in corpus]

    X_train, X_test, y_train, y_test = grouped_train_test_split(
        texts, labels, template_ids, test_size=0.3, seed=42
    )

    # Rebuild the template-id sets from the split indices.
    train_tids = {
        tid for p, tid in zip(corpus, template_ids, strict=False) if p.text in set(X_train)
    }
    test_tids = {tid for p, tid in zip(corpus, template_ids, strict=False) if p.text in set(X_test)}

    # The two sets must be completely disjoint — the whole point of grouped holdout.
    assert train_tids.isdisjoint(test_tids), (
        "Template IDs appear in both train and test: " f"{train_tids & test_tids}"
    )
    # Both splits must be non-empty.
    assert X_train and X_test


def test_grouped_split_fallback_no_ids() -> None:
    """grouped_train_test_split falls back to stratified split when template_ids=None."""
    corpus = build_corpus()
    texts = [p.text for p in corpus]
    labels = [p.label for p in corpus]

    X_train, X_test, y_train, y_test = grouped_train_test_split(
        texts, labels, template_ids=None, test_size=0.3, seed=42
    )

    total = len(texts)
    assert len(X_train) + len(X_test) == total, "All samples must be assigned to a split"
    assert X_train and X_test, "Both splits must be non-empty"
    # Each split retains both classes (stratified).
    assert LABEL_ADVERSARIAL in y_train and LABEL_BENIGN in y_train
    assert LABEL_ADVERSARIAL in y_test and LABEL_BENIGN in y_test


def test_evaluate_with_holdout_returns_honest_f1() -> None:
    """evaluate_with_holdout must actually split: n_train and n_test < total."""
    from redteam.detector import DetectorConfig, RedTeamDetector

    corpus = build_corpus()
    texts = [p.text for p in corpus]
    labels = [p.label for p in corpus]
    template_ids = [p.template_id for p in corpus]
    total = len(texts)

    detector = RedTeamDetector(config=DetectorConfig(random_state=42))
    result = evaluate_with_holdout(detector, texts, labels, template_ids=template_ids)

    # Verify expected keys are present.
    for key in ("precision", "recall", "f1", "n_train", "n_test", "split_method"):
        assert key in result, f"Missing key in result: {key}"

    # n_train and n_test must each be strictly less than the full corpus size,
    # confirming the data was actually split rather than evaluated on itself.
    assert result["n_train"] < total, f"n_train ({result['n_train']}) should be < total ({total})"
    assert result["n_test"] < total, f"n_test ({result['n_test']}) should be < total ({total})"
    assert result["n_train"] + result["n_test"] == total

    # Grouped split was requested, so the method must be reported correctly.
    assert result["split_method"] == "grouped"

    # Sanity-check metric ranges.
    assert 0.0 <= result["f1"] <= 1.0
    assert 0.0 <= result["precision"] <= 1.0
    assert 0.0 <= result["recall"] <= 1.0

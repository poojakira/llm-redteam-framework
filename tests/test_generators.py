"""Seed-pinned tests for the adversarial-prompt generators."""

from __future__ import annotations

import random

import pytest

from redteam.generators import (
    BENIGN_CATEGORY,
    GENERATORS,
    LABEL_ADVERSARIAL,
    LABEL_BENIGN,
    AttackCategory,
    GeneratedPrompt,
    build_corpus,
    gen_benign,
)

SEED = 20240713


def test_all_six_categories_present() -> None:
    assert set(GENERATORS) == set(AttackCategory.all())
    assert len(GENERATORS) == 6


@pytest.mark.parametrize("category", AttackCategory.all())
def test_generator_returns_text_and_prefixed_template_id(category: AttackCategory) -> None:
    rng = random.Random(SEED)
    text, template_id = GENERATORS[category](rng)
    assert isinstance(text, str) and text.strip()
    assert template_id.split(":", 1)[0] == category.value


def test_generators_are_deterministic_given_seed() -> None:
    a = GENERATORS[AttackCategory.DIRECT_OVERRIDE](random.Random(1))
    b = GENERATORS[AttackCategory.DIRECT_OVERRIDE](random.Random(1))
    assert a == b


def test_benign_generator_labels_and_prefix() -> None:
    text, template_id = gen_benign(random.Random(SEED))
    assert text.strip()
    assert template_id.startswith("benign_")


def test_build_corpus_is_reproducible() -> None:
    c1 = build_corpus(seed=SEED)
    c2 = build_corpus(seed=SEED)
    assert [p.text for p in c1] == [p.text for p in c2]


def test_build_corpus_composition() -> None:
    corpus = build_corpus(seed=SEED)
    # Six attack categories at 120 unique each + benign remainder.
    per_cat = {cat.value: 0 for cat in AttackCategory.all()}
    n_benign = 0
    for p in corpus:
        assert isinstance(p, GeneratedPrompt)
        if p.category == BENIGN_CATEGORY:
            assert p.label == LABEL_BENIGN
            n_benign += 1
        else:
            assert p.label == LABEL_ADVERSARIAL
            per_cat[p.category] += 1
    assert all(v == 120 for v in per_cat.values())
    assert n_benign > 200  # ample benign for FP-rate measurement
    # Corpus texts are unique (deduplicated).
    texts = [p.text for p in corpus]
    assert len(texts) == len(set(texts))


def test_gen_benign_produces_hard_negatives() -> None:
    """Some benign samples must quote attack vocabulary (hard negatives)."""
    rng = random.Random(SEED)
    prefixes = {gen_benign(rng)[1].split(":", 1)[0] for _ in range(400)}
    assert "benign_hardneg" in prefixes
    assert "benign_embed" in prefixes
    assert "benign_normal" in prefixes

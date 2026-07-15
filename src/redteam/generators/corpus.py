"""Build a labelled corpus of adversarial and benign prompts."""

from __future__ import annotations

import random

from .base import (
    BENIGN_CATEGORY,
    LABEL_ADVERSARIAL,
    LABEL_BENIGN,
    AttackCategory,
    GeneratedPrompt,
)
from .categories import GENERATORS, gen_benign


def _unique_samples(
    factory,
    count: int,
    rng: random.Random,
    label: int,
    category: str,
    max_attempts_factor: int = 50,
) -> list[GeneratedPrompt]:
    """Draw ``count`` de-duplicated samples from ``factory``.

    ``factory`` returns ``(text, template_id)``. Sampling stops early
    (returning fewer than ``count``) if the generator's combinatorial space is
    exhausted, which keeps generation terminating.
    """
    seen: set[str] = set()
    out: list[GeneratedPrompt] = []
    attempts = 0
    limit = count * max_attempts_factor
    while len(out) < count and attempts < limit:
        text, template_id = factory(rng)
        attempts += 1
        if text in seen:
            continue
        seen.add(text)
        out.append(
            GeneratedPrompt(
                text=text,
                label=label,
                category=category,
                template_id=template_id,
            )
        )
    return out


def build_corpus(
    n_adversarial_per_category: int = 120,
    n_benign: int = 720,
    seed: int = 20240713,
) -> list[GeneratedPrompt]:
    """Generate a reproducible labelled corpus.

    Parameters
    ----------
    n_adversarial_per_category:
        Number of prompts to draw from each of the six attack categories.
    n_benign:
        Target number of benign prompts (used both for training and for measuring the
        false-positive rate on held-out benign text).
    seed:
        Seed for the internal ``random.Random`` -- fixing it makes the corpus,
        and therefore all downstream metrics, reproducible.

    Returns
    -------
    list[GeneratedPrompt]
        Shuffled list of labelled prompts.
    """
    ## Deterministic corpus generation; not used for cryptography.
    rng = random.Random(seed)  # nosec B311
    corpus: list[GeneratedPrompt] = []

    for category in AttackCategory.all():
        corpus.extend(
            _unique_samples(
                GENERATORS[category],
                n_adversarial_per_category,
                rng,
                LABEL_ADVERSARIAL,
                category.value,
            )
        )

    corpus.extend(
        _unique_samples(
            gen_benign,
            n_benign,
            rng,
            LABEL_BENIGN,
            BENIGN_CATEGORY,
        )
    )

    rng.shuffle(corpus)
    return corpus

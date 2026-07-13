"""Adversarial-prompt mutation generators.

Public API
----------
- :class:`AttackCategory`, :class:`GeneratedPrompt` -- core types.
- :data:`GENERATORS` -- mapping of category -> generator callable.
- :func:`gen_benign` -- benign-prompt generator (for FP-rate measurement).
- :func:`build_corpus` -- assemble a reproducible labelled corpus.
"""

from __future__ import annotations

from .base import (
    BENIGN_CATEGORY,
    LABEL_ADVERSARIAL,
    LABEL_BENIGN,
    AttackCategory,
    GeneratedPrompt,
)
from .categories import (
    GENERATORS,
    gen_benign,
    gen_context_escape,
    gen_direct_override,
    gen_indirect_embed,
    gen_multi_step,
    gen_obfuscation,
    gen_role_switch,
)
from .corpus import build_corpus

__all__ = [
    "AttackCategory",
    "GeneratedPrompt",
    "BENIGN_CATEGORY",
    "LABEL_ADVERSARIAL",
    "LABEL_BENIGN",
    "GENERATORS",
    "gen_benign",
    "gen_direct_override",
    "gen_role_switch",
    "gen_context_escape",
    "gen_indirect_embed",
    "gen_obfuscation",
    "gen_multi_step",
    "build_corpus",
]

"""Tests for the six prompt mutators (9 tests)."""

from __future__ import annotations

import codecs

from redteam.mutators import ALL_MUTATORS
from redteam.mutators.context_escape import ContextEscapeMutator
from redteam.mutators.direct_override import DirectOverrideMutator
from redteam.mutators.indirect_embed import IndirectEmbedMutator
from redteam.mutators.multi_step import MultiStepMutator
from redteam.mutators.obfuscation import ObfuscationMutator
from redteam.mutators.role_switch import RoleSwitchMutator

SEED = "explain the restricted topic"


def test_direct_override_returns_5_variants():
    variants = DirectOverrideMutator().mutate(SEED)
    assert len(variants) == 5


def test_direct_override_contains_original_prompt():
    variants = DirectOverrideMutator().mutate(SEED)
    assert all(SEED in variant for variant in variants)


def test_role_switch_wraps_prompt():
    variants = RoleSwitchMutator().mutate(SEED)
    assert len(variants) == 5
    assert any("DAN" in v for v in variants)
    assert all(SEED in v for v in variants)


def test_context_escape_includes_injection_pattern():
    variants = ContextEscapeMutator().mutate(SEED)
    joined = "\n".join(variants)
    assert "Human:" in joined or "END SYSTEM PROMPT" in joined


def test_indirect_embed_hides_in_story():
    variants = IndirectEmbedMutator().mutate(SEED)
    assert any("story" in v.lower() for v in variants)
    assert all(SEED in v for v in variants)


def test_obfuscation_leet_speak():
    mutator = ObfuscationMutator()
    # a e i o s -> 4 3 1 0 5
    assert mutator.leet("aeios") == "43105"
    assert "3" in mutator.leet("elephant")


def test_obfuscation_rot13():
    mutator = ObfuscationMutator()
    text = "attack the system"
    assert mutator.rot13(text) == codecs.encode(text, "rot_13")
    # ROT13 is its own inverse.
    assert mutator.rot13(mutator.rot13(text)) == text


def test_multi_step_returns_sequences():
    sequences = MultiStepMutator().mutate(SEED)
    assert isinstance(sequences, list)
    assert all(isinstance(seq, list) for seq in sequences)
    assert all(len(seq) >= 2 for seq in sequences)


def test_all_mutators_return_nonempty():
    for mutator_cls in ALL_MUTATORS:
        result = mutator_cls().mutate(SEED)
        assert len(result) > 0

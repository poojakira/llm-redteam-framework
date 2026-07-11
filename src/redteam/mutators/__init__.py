"""Prompt mutators.

Each mutator takes a seed prompt and produces adversarial variants that exercise a
distinct jailbreak *tactic*. The categories mirror patterns catalogued in public
red-teaming literature (e.g. WildTeaming, arXiv:2406.18510) rather than inventing novel
exploits: the goal is to reproduce known failure modes so a detector can be trained and
tested against them offline.
"""

from redteam.mutators.context_escape import ContextEscapeMutator
from redteam.mutators.direct_override import DirectOverrideMutator
from redteam.mutators.indirect_embed import IndirectEmbedMutator
from redteam.mutators.multi_step import MultiStepMutator
from redteam.mutators.obfuscation import ObfuscationMutator
from redteam.mutators.role_switch import RoleSwitchMutator

ALL_MUTATORS = [
    DirectOverrideMutator,
    RoleSwitchMutator,
    ContextEscapeMutator,
    IndirectEmbedMutator,
    ObfuscationMutator,
    MultiStepMutator,
]

__all__ = [
    "DirectOverrideMutator",
    "RoleSwitchMutator",
    "ContextEscapeMutator",
    "IndirectEmbedMutator",
    "ObfuscationMutator",
    "MultiStepMutator",
    "ALL_MUTATORS",
]

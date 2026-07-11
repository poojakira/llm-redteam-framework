"""llm-redteam-framework: an offline LLM red-teaming toolkit.

Two halves:

* ``mutators`` and ``RedTeamGenerator`` -- produce adversarial prompt variants across
  six jailbreak tactics.
* ``AdversarialDetector`` -- a fast, interpretable TF-IDF detector trained to flag them.

Everything runs locally with no LLM API and no network access.
"""

from redteam.detector.tfidf_classifier import AdversarialDetector
from redteam.generator import RedTeamGenerator
from redteam.mutators import (
    ALL_MUTATORS,
    ContextEscapeMutator,
    DirectOverrideMutator,
    IndirectEmbedMutator,
    MultiStepMutator,
    ObfuscationMutator,
    RoleSwitchMutator,
)

__all__ = [
    "RedTeamGenerator",
    "AdversarialDetector",
    "DirectOverrideMutator",
    "RoleSwitchMutator",
    "ContextEscapeMutator",
    "IndirectEmbedMutator",
    "ObfuscationMutator",
    "MultiStepMutator",
    "ALL_MUTATORS",
]

__version__ = "0.1.0"

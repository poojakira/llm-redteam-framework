"""Core types shared across the adversarial-prompt generators."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttackCategory(str, Enum):
    """Taxonomy of adversarial-prompt mutation strategies."""

    DIRECT_OVERRIDE = "direct_override"
    ROLE_SWITCH = "role_switch"
    CONTEXT_ESCAPE = "context_escape"
    INDIRECT_EMBED = "indirect_embed"
    OBFUSCATION = "obfuscation"
    MULTI_STEP = "multi_step"

    @classmethod
    def all(cls) -> list["AttackCategory"]:
        """Return every attack category in declaration order."""
        return list(cls)


# Label constants for the binary detection task.
LABEL_ADVERSARIAL: int = 1
LABEL_BENIGN: int = 0

# Sentinel category assigned to benign (non-attack) samples.
BENIGN_CATEGORY: str = "benign"


@dataclass(frozen=True)
class GeneratedPrompt:
    """A single labelled prompt produced by the generators.

    Attributes
    ----------
    text:
        The prompt text.
    label:
        ``1`` for an adversarial prompt, ``0`` for benign text.
    category:
        The :class:`AttackCategory` value that produced the prompt, or
        :data:`BENIGN_CATEGORY` for benign samples.
    template_id:
        Stable identifier of the template that produced the prompt. Used by the
        evaluation harness to build a *leave-templates-out* split so that the
        held-out set contains templates unseen during training.
    """

    text: str
    label: int
    category: str
    template_id: str = ""

    def __post_init__(self) -> None:
        if self.label not in (LABEL_BENIGN, LABEL_ADVERSARIAL):
            raise ValueError(f"label must be 0 or 1, got {self.label!r}")
        if not self.text or not self.text.strip():
            raise ValueError("text must be a non-empty string")

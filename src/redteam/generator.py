"""RedTeamGenerator: orchestrate every mutator into datasets and reports.

The generator turns a handful of seed prompts into a labelled corpus: it applies each
mutator, tags every output with its source mutator and a coarse adversarial score, and
can emit a ``(prompts, labels)`` pair ready to train the detector.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from redteam.mutators import ALL_MUTATORS
from redteam.mutators.multi_step import MultiStepMutator


class RedTeamGenerator:
    """Compose all mutators and produce labelled adversarial datasets."""

    def __init__(self, mutators: list[Any] | None = None) -> None:
        if mutators is None:
            mutators = [mutator_cls() for mutator_cls in ALL_MUTATORS]
        self.mutators = mutators

    @staticmethod
    def _flatten(variant: Any) -> str:
        """Render a mutator output (string or multi-turn sequence) as one string."""
        if isinstance(variant, (list, tuple)):
            return "\n".join(str(turn) for turn in variant)
        return str(variant)

    def generate(self, seed_prompt: str, n_per_mutator: int = 5) -> list[dict]:
        """Return ``{prompt, mutator, seed, adversarial_score}`` records.

        ``adversarial_score`` is a fixed high prior (0.9): everything a mutator emits is
        an adversarial attempt by construction. It exists so downstream consumers can
        weight or threshold records uniformly.
        """
        records: list[dict] = []
        for mutator in self.mutators:
            variants = mutator.mutate(seed_prompt)[:n_per_mutator]
            for variant in variants:
                records.append(
                    {
                        "prompt": self._flatten(variant),
                        "mutator": getattr(mutator, "name", type(mutator).__name__),
                        "seed": seed_prompt,
                        "adversarial_score": 0.9,
                    }
                )
        return records

    def generate_dataset(
        self,
        seeds: Sequence[str],
        benign: Sequence[str] | None = None,
    ) -> tuple[list[str], list[int]]:
        """Build a ``(prompts, labels)`` corpus suitable for training the detector.

        Every mutated seed is labelled 1 (adversarial). Any ``benign`` prompts supplied
        are labelled 0. Passing benign prompts is what makes the corpus trainable; on
        its own the adversarial half has no negative class.
        """
        prompts: list[str] = []
        labels: list[int] = []
        for seed in seeds:
            for record in self.generate(seed):
                prompts.append(record["prompt"])
                labels.append(1)
        if benign:
            for text in benign:
                prompts.append(str(text))
                labels.append(0)
        return prompts, labels

    def from_file(self, path: str) -> list[dict]:
        """Read newline-separated seeds from ``path`` and generate records for each.

        Blank lines and lines starting with ``#`` are ignored.
        """
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        seeds = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
        records: list[dict] = []
        for seed in seeds:
            records.extend(self.generate(seed))
        return records

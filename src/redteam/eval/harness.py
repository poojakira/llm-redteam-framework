"""Held-out evaluation harness for the adversarial-prompt detector.

The harness builds a labelled corpus, splits it into disjoint train / test
sets, trains the detector on the train split only, and reports
precision / recall / F1 for the adversarial class **plus** the false-positive
rate measured on held-out benign text.

Two split strategies are supported:

``"grouped"`` (default)
    *Leave-templates-out*: entire template groups are held out, so the test set
    contains templates never seen during training. This measures generalization
    to novel phrasings and is the honest, harder metric.

``"random"``
    A stratified random split. Because the template-based generator reuses
    templates across the split, this yields optimistic, in-distribution numbers
    and is provided mainly for comparison.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from math import ceil
from pathlib import Path

import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from ..detector import DetectorConfig, RedTeamDetector
from ..generators import (
    LABEL_ADVERSARIAL,
    LABEL_BENIGN,
    GeneratedPrompt,
    build_corpus,
)


@dataclass(frozen=True)
class EvalReport:
    """Held-out evaluation metrics.

    All figures are computed on the test split, which is disjoint from the data
    the detector was trained on.
    """

    split_mode: str
    precision: float
    recall: float
    f1: float
    false_positive_rate: float
    accuracy: float
    n_total: int
    n_train: int
    n_test: int
    n_test_adversarial: int
    n_test_benign: int
    n_test_templates: int
    false_positives: int
    false_negatives: int
    seed: int

    def to_dict(self) -> dict:
        """Return the report as a plain dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize the report to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def _template_prefix(template_id: str) -> str:
    """Group key: the part of a template id before the first ``':'``."""
    return template_id.split(":", 1)[0]


def _grouped_split(
    corpus: list[GeneratedPrompt],
    test_size: float,
    seed: int,
) -> tuple[list[GeneratedPrompt], list[GeneratedPrompt]]:
    """Leave-templates-out split.

    Within each template-prefix group (e.g. ``direct_override``,
    ``benign_normal``) a ``test_size`` fraction of the distinct templates is
    assigned to the test split; the rest go to train. This guarantees every
    category is represented on both sides while keeping test templates unseen
    during training.
    """
    ## Deterministic evaluation split; not used for cryptography.
    rng = random.Random(seed)  # nosec B311
    prefix_to_templates: dict[str, set[str]] = defaultdict(set)
    for p in corpus:
        prefix_to_templates[_template_prefix(p.template_id)].add(p.template_id)

    test_templates: set[str] = set()
    for prefix, templates in prefix_to_templates.items():
        ordered = sorted(templates)
        rng.shuffle(ordered)
        n_test = ceil(len(ordered) * test_size)
        # Keep at least one template for training when a group is splittable.
        if len(ordered) >= 2:
            n_test = min(n_test, len(ordered) - 1)
        test_templates.update(ordered[:n_test])

    train = [p for p in corpus if p.template_id not in test_templates]
    test = [p for p in corpus if p.template_id in test_templates]
    return train, test


def evaluate(
    split_mode: str = "grouped",
    test_size: float = 0.3,
    seed: int = 42,
    corpus_seed: int = 20240713,
    detector_config: DetectorConfig | None = None,
) -> tuple[EvalReport, RedTeamDetector]:
    """Run a full held-out evaluation.

    Parameters
    ----------
    split_mode:
        ``"grouped"`` (leave-templates-out, default) or ``"random"``.
    test_size:
        Fraction of the corpus (grouped: of the templates) reserved for test.
    seed:
        Seed controlling the split (fixed for reproducibility).
    corpus_seed:
        Seed passed to :func:`build_corpus`.
    detector_config:
        Optional detector hyper-parameters.

    Returns
    -------
    tuple[EvalReport, RedTeamDetector]
        The metrics report and the trained detector.
    """
    corpus = build_corpus(seed=corpus_seed)

    x_train: list[str]
    x_test: list[str]
    y_train: np.ndarray
    y_test: np.ndarray

    if split_mode == "grouped":
        train_items, test_items = _grouped_split(corpus, test_size, seed)
        x_train = [p.text for p in train_items]
        y_train = np.array([p.label for p in train_items], dtype=int)
        x_test = [p.text for p in test_items]
        y_test = np.array([p.label for p in test_items], dtype=int)
        n_test_templates = len({p.template_id for p in test_items})
    elif split_mode == "random":
        texts = [p.text for p in corpus]
        labels = np.array([p.label for p in corpus], dtype=int)
        split = train_test_split(
            texts, labels, test_size=test_size, random_state=seed, stratify=labels
        )
        x_train = list(split[0])
        x_test = list(split[1])
        y_train = np.asarray(split[2], dtype=int)
        y_test = np.asarray(split[3], dtype=int)
        n_test_templates = -1  # not meaningful for a random split
    else:
        raise ValueError(f"unknown split_mode: {split_mode!r}")

    detector = RedTeamDetector(config=detector_config)
    detector.train(x_train, y_train)
    y_pred = detector.predict(x_test)

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        y_pred,
        labels=[LABEL_ADVERSARIAL],
        average="binary",
        pos_label=LABEL_ADVERSARIAL,
        zero_division=0,  # type: ignore[reportArgumentType]
    )

    benign_mask = y_test == LABEL_BENIGN
    n_benign = int(benign_mask.sum())
    false_positives = int(np.sum((y_pred == LABEL_ADVERSARIAL) & benign_mask))
    fp_rate = float(false_positives / n_benign) if n_benign else 0.0

    adv_mask = y_test == LABEL_ADVERSARIAL
    false_negatives = int(np.sum((y_pred == LABEL_BENIGN) & adv_mask))
    accuracy = float(np.mean(y_pred == y_test))

    report = EvalReport(
        split_mode=split_mode,
        precision=float(precision),
        recall=float(recall),
        f1=float(f1),
        false_positive_rate=fp_rate,
        accuracy=accuracy,
        n_total=len(corpus),
        n_train=len(x_train),
        n_test=len(x_test),
        n_test_adversarial=int(adv_mask.sum()),
        n_test_benign=n_benign,
        n_test_templates=n_test_templates,
        false_positives=false_positives,
        false_negatives=false_negatives,
        seed=seed,
    )
    return report, detector


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: run the evaluation and print / save the JSON report."""
    parser = argparse.ArgumentParser(description="Run held-out detector evaluation.")
    parser.add_argument("--split-mode", choices=["grouped", "random"], default="grouped")
    parser.add_argument("--test-size", type=float, default=0.3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--corpus-seed", type=int, default=20240713)
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to write the JSON report.",
    )
    args = parser.parse_args(argv)

    report, _ = evaluate(
        split_mode=args.split_mode,
        test_size=args.test_size,
        seed=args.seed,
        corpus_seed=args.corpus_seed,
    )
    print(report.to_json())
    if args.output:
        Path(args.output).write_text(report.to_json(), encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

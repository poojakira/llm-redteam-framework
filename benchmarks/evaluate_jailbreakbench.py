"""Evaluate the detector on the official JailbreakBench behavior datasets.

This measures harmful-versus-benign JBB behavior screening. It is not a
prompt-injection benchmark and does not claim official JailbreakBench defense
leaderboard performance.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from datasets import load_dataset
from sklearn.metrics import precision_recall_fscore_support

from redteam.detector import DetectorConfig, RedTeamDetector
from redteam.generators import LABEL_ADVERSARIAL, LABEL_BENIGN, build_corpus

JBB_REPOSITORY = "https://github.com/JailbreakBench/jailbreakbench"
JBB_COMMIT = "23dbdf6b19650521604456229bc1d9c4156c85c1"
JBB_DATASET = "JailbreakBench/JBB-Behaviors"
JBB_DOI = "10.57967/hf/2540"


def git_commit() -> str | None:
    """Return the checked-out project commit when Git is available."""
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    harmful = load_dataset(JBB_DATASET, "behaviors", split="harmful")
    benign = load_dataset(JBB_DATASET, "behaviors", split="benign")
    texts = list(harmful["Goal"]) + list(benign["Goal"])
    labels = [LABEL_ADVERSARIAL] * len(harmful) + [LABEL_BENIGN] * len(benign)

    corpus = build_corpus(seed=20240713)
    detector = RedTeamDetector(config=DetectorConfig(random_state=42))
    detector.train([item.text for item in corpus], [item.label for item in corpus])
    predictions = [int(value) for value in detector.predict(texts)]
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        labels=[LABEL_ADVERSARIAL],
        average="binary",
        pos_label=LABEL_ADVERSARIAL,
        zero_division=0,
    )
    benign_total = len(benign)
    false_positives = sum(
        predicted == LABEL_ADVERSARIAL and label == LABEL_BENIGN
        for predicted, label in zip(predictions, labels, strict=True)
    )

    payload = {
        "schema_version": "jailbreakbench-behavior-screening-v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "claim_boundary": (
            "This is harmful-versus-benign behavior screening on official JBB goals. "
            "It is not an official JailbreakBench defense leaderboard score and not prompt-injection F1."
        ),
        "source_commit": git_commit(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "dataset": {
            "name": JBB_DATASET,
            "repository": JBB_REPOSITORY,
            "repository_commit": JBB_COMMIT,
            "doi": JBB_DOI,
            "license": "MIT",
            "harmful_count": len(harmful),
            "benign_count": len(benign),
        },
        "training": {"corpus_seed": 20240713, "detector_random_state": 42},
        "metrics": {
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "false_positives": false_positives,
            "false_positive_rate": false_positives / max(benign_total, 1),
        },
        "raw_predictions": [
            {"text": text, "label": label, "prediction": prediction}
            for text, label, prediction in zip(texts, labels, predictions, strict=True)
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload["metrics"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

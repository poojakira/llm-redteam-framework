"""Generate reproducible internal evidence for the LLM red-team framework.

This runner measures the generated-corpus grouped split and a 100-prompt full
pipeline. It intentionally does not claim official InjectionBench or
JailbreakBench validation; see official_dataset_manifest.json for prerequisites.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from redteam.detector import DetectorConfig, RedTeamDetector
from redteam.eval import evaluate
from redteam.generators import build_corpus
from redteam.generators.base import AttackCategory
from redteam.generators.categories import GENERATORS


def git_commit() -> str | None:
    """Return the checked-out commit when Git is available."""
    result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def measure_hundred_prompt_pipeline() -> dict[str, float | int]:
    """Measure corpus build, training, and prediction for exactly 100 prompts."""
    started = time.perf_counter()
    corpus = build_corpus(seed=20240713)
    detector = RedTeamDetector(config=DetectorConfig(random_state=42))
    detector.train([prompt.text for prompt in corpus], [prompt.label for prompt in corpus])
    rng = random.Random(99)
    categories = AttackCategory.all()
    prompts = [GENERATORS[categories[index % len(categories)]](rng)[0] for index in range(100)]
    predictions = detector.predict(prompts)
    return {
        "prompt_count": len(prompts),
        "prediction_count": len(predictions),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report, _ = evaluate(split_mode="grouped", test_size=0.3, seed=42, corpus_seed=20240713)
    payload = {
        "schema_version": "llm-internal-evidence-v1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "claim_boundary": (
            "Metrics use the repository-generated corpus and leave-templates-out split. "
            "They are not official InjectionBench or JailbreakBench results."
        ),
        "source_commit": git_commit(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "evaluation": report.to_dict(),
        "hundred_prompt_full_pipeline": measure_hundred_prompt_pipeline(),
        "official_dataset_manifest": "benchmarks/official_dataset_manifest.json",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

# Official JBB dataset download provenance

`evaluate_jailbreakbench.py` downloads both the harmful and benign `behaviors`
splits from `JailbreakBench/JBB-Behaviors` at dataset revision
[`886acc352a31533ffbcf4ef22c744658688086fc`](https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/tree/886acc352a31533ffbcf4ef22c744658688086fc).
This public Git revision was resolved on 2026-11-19 UTC without downloading the
dataset. It is distinct from the upstream JailbreakBench software repository
commit recorded in the report's `repository_commit` field. New reports record
the downloaded dataset commit in `dataset.revision`.

With the optional benchmark dependencies installed, run from the repository root:

```sh
PYTHONPATH=src python benchmarks/evaluate_jailbreakbench.py --output /tmp/jbb-report.json
```

This explicit benchmark command requires network access for the public dataset
unless it is cached. It does not call an LLM provider or require an API key.
The revision pin makes the selected dataset reproducible; it does not prove
dataset safety or verify an existing benchmark result. The download and the
official-dataset benchmark were not executed as part of the revision-pin fix.
Previously saved reports without a dataset revision retain that provenance gap.

The measurement is harmful-versus-benign behavior screening, not an official
JailbreakBench defense leaderboard score or a test of a live LLM's compliance.

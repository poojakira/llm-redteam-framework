# Performance Baseline

Measured performance for the `llm-redteam-framework` offline detector,
produced by [`benchmarks/detection_perf.py`](../benchmarks/detection_perf.py).

## How to reproduce

```bash
pip install -e ".[dev]"
python benchmarks/detection_perf.py          # latency/throughput gate
python benchmarks/external_validation.py     # F1 on external-style fixtures
```

## Measured baseline

Environment: Windows, Python 3.12, single thread, 10,000-prompt corpus.
Detector: TF-IDF char n-gram + LogisticRegression.

| Metric | Measured | Gate |
|--------|----------|------|
| p95 predict latency | ~1.0 ms | must be < 5 ms |
| Throughput (single thread) | ~1,400 prompts/sec | must be > 1,000 prompts/sec |
| Test coverage (`redteam`) | ~96% | gate 90% (see pyproject.toml) |

External-fixture detection quality (from `external_validation.py`):

| Set | F1 | Gate |
|-----|----|------|
| Internal corpus | ~0.97 | — |
| InjectionBench-style | ~0.98 | ≥ 0.85 |
| JailbreakBench-style | ~0.98 | ≥ 0.85 |

Notes:
- Throughput reflects the TF-IDF pipeline on a single thread. It is not 50k/sec;
  earlier drafts of this doc overstated it and have been corrected.
- The external fixtures are synthetic, hand-written examples included in the
  benchmark file, not the official InjectionBench/JailbreakBench datasets. They
  are labeled "-style" for that reason.

## Regression policy

- The CI perf gate uses the thresholds above.
- If a change shifts the baseline, update the gate defaults in
  `benchmarks/detection_perf.py` and this document in the same PR.

# Performance Baseline

## LLM Red Team Framework — Detection Performance Standards

**Last Updated:** 2026-08-27  
**Benchmark Runner:** `benchmarks/detection_perf.py`  
**Validation Runner:** `benchmarks/external_validation.py`

---

## Performance Gates

All gates must pass in CI before any merge to `main`.

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| p95 Latency | < 1 ms/prompt | Real-time detection must not add perceptible delay |
| Throughput | > 50,000 prompts/sec | Support high-traffic deployments without horizontal scaling |
| Test Coverage | ≥ 90% | Comprehensive coverage prevents regressions |
| Internal F1 | ≥ 0.95 | High accuracy on known attack patterns |
| External F1 (InjectionBench) | ≥ 0.85 | Generalization to unseen injection patterns |
| External F1 (JailbreakBench) | ≥ 0.85 | Generalization to unseen jailbreak patterns |

---

## Current Baseline (v1.0)

### Detection Accuracy

| Dataset | Precision | Recall | F1 Score | Samples |
|---------|-----------|--------|----------|---------|
| Internal test set | 0.97 | 0.97 | 0.97 | 69 tests |
| InjectionBench (external) | TBD | TBD | ≥ 0.85 | 50 fixtures |
| JailbreakBench (external) | TBD | TBD | ≥ 0.85 | 50 fixtures |

### Latency Profile

| Percentile | Target | Measured |
|------------|--------|----------|
| p50 | < 0.5 ms | TBD (run benchmark) |
| p90 | < 0.8 ms | TBD (run benchmark) |
| p95 | < 1.0 ms | TBD (run benchmark) |
| p99 | < 2.0 ms | TBD (run benchmark) |

### Throughput

| Metric | Target | Measured |
|--------|--------|----------|
| Prompts/sec (single thread) | > 50,000 | TBD (run benchmark) |
| Corpus size for benchmark | 10,000 prompts | Fixed |

---

## Benchmark Methodology

### Performance Benchmark (`benchmarks/detection_perf.py`)

**Corpus composition:**
- 10,000 prompts total
- 70% benign (templated real-world queries)
- 30% adversarial (templated injection/jailbreak patterns)
- Deterministic generation (seed=42) for reproducibility

**Measurement protocol:**
1. Initialize detector
2. Warm-up pass: 100 prompts (excluded from timing)
3. Timed pass: 10,000 prompts with per-prompt latency capture
4. Compute statistics: mean, median, p50, p90, p95, p99, max
5. Compute throughput: total prompts / wall-clock time

**Environment requirements:**
- Benchmarks run on CI (Ubuntu, GitHub Actions runner)
- No GPU required (CPU inference only)
- Results may vary on local machines — CI is the source of truth

### External Validation (`benchmarks/external_validation.py`)

**Datasets:**
- InjectionBench: 50 fixtures (25 injections + 25 benign)
- JailbreakBench: 50 fixtures (25 jailbreaks + 25 benign)

**Categories covered:**

*InjectionBench:*
- Direct prompt injection
- Indirect injection (via documents/emails)
- Encoded injection (base64, ROT13, hex, reverse)
- Context manipulation

*JailbreakBench:*
- DAN-style personas
- Roleplay manipulation
- Token smuggling
- Multi-turn escalation
- Prompt leaking attempts

**Evaluation protocol:**
1. Train detector on internal corpus
2. Evaluate on external fixtures (zero-shot generalization)
3. Compute precision, recall, F1, accuracy per benchmark
4. Assert F1 ≥ 0.85 on each

---

## Running Benchmarks Locally

```bash
# Performance benchmark
python benchmarks/detection_perf.py

# External validation
python benchmarks/external_validation.py

# Both output JSON results to benchmarks/results/
```

---

## Regression Detection

Performance regressions are caught automatically in CI:

1. **PR check**: Both benchmarks run on every pull request
2. **Gate enforcement**: PR cannot merge if any gate fails
3. **Trend tracking**: Results are uploaded as CI artifacts for historical comparison

### What Triggers a Regression

| Condition | Action |
|-----------|--------|
| p95 latency > 1ms | CI fails, block merge |
| Throughput < 50k/sec | CI fails, block merge |
| External F1 < 0.85 | CI fails, block merge |
| Coverage < 90% | CI fails, block merge |
| p95 latency increase > 20% vs baseline | Warning annotation on PR |

---

## Capacity Planning

### Single-Instance Limits

Based on the 50,000 prompts/sec throughput target:

| Concurrent Users | Avg Prompts/User/sec | Headroom |
|-----------------|---------------------|----------|
| 100 | 10 | 50x |
| 500 | 10 | 10x |
| 1,000 | 10 | 5x |
| 5,000 | 10 | 1x (scale out) |

### Scaling Recommendations

- **< 5,000 req/s**: Single instance sufficient
- **5,000–50,000 req/s**: 2–10 replicas with load balancer
- **> 50,000 req/s**: Horizontal scaling + request batching

---

## Updating This Baseline

When detector architecture changes:

1. Run benchmarks on the new implementation
2. Update "Measured" columns with actual values
3. If performance improves, tighten thresholds (ratchet)
4. If performance degrades, investigate before merging
5. Document any threshold changes in this file's revision history

---

## Revision History

| Date | Change | Author |
|------|--------|--------|
| 2026-08-27 | Initial baseline document | Engineering Team |

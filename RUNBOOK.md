# RUNBOOK  --  LLM Red Team Framework

## Prerequisites

- Python 3.10+
- API key for target LLM (OpenAI, Anthropic, etc.) if testing live models
- Optional: GPU for local model evaluation

## Install

```bash
git clone <repo-url> && cd llm-redteam-framework
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Set target model credentials (optional, for live model testing only)
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run the Evaluation

The `redteam-eval` command generates the adversarial + benign corpus, trains the
offline detector, and scores it on a held-out split in one pass.

```bash
# Grouped split (default)  --  prevents template leakage between train/test
redteam-eval --output eval.json

# Random split with a fixed seed for reproducibility
redteam-eval --split-mode random --test-size 0.3 --seed 42 --output eval.json

# Vary the corpus generation seed
redteam-eval --corpus-seed 7 --output eval.json
```

Output JSON includes `precision`, `recall`, `f1`, `false_positive_rate`,
`accuracy`, `n_total`, `n_train`, and `n_test`.

## Measure Out-of-Distribution Degradation

The grouped/random splits share template *families*. To measure the honest
generalization ceiling against natural-language paraphrases with no structural
tells, run the OOD benchmark:

```bash
python benchmarks/ood_novel_phrasings.py
```

Current deterministic result: precision 0.5897, recall 0.92, **F1 0.7188**, accuracy
0.64 — a reproducible ~25-point drop from the grouped reference F1 of 0.9714. The
result is written to `benchmarks/results/ood_novel_phrasings_results.json` and
pinned in `tests/test_ood_benchmark.py`.

## Run the API Server

```bash
# Protected endpoints fail closed unless REDTEAM_API_KEY is configured.
export REDTEAM_API_KEY="$(openssl rand -hex 32)"
uvicorn redteam.api.app:app --host 0.0.0.0 --port 8000

# Health check remains unauthenticated for orchestration probes.
curl http://localhost:8000/health

# Scan with API key auth
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"prompt": "Test prompt"}'
```

### Security Configuration

The `/scan` endpoint implements three layers of security controls. All are configured
via `llm-security-config.yaml` and/or environment variables.

#### Rate Limiting

In-memory per-IP sliding-window rate limiter. No external dependencies (Redis, etc.).

| Setting | Default | Config Key |
|---------|---------|------------|
| Max requests/minute | 60 | `rate_limiting.max_requests_per_minute` |
| Max prompt length | 32768 chars | `rate_limiting.max_prompt_length_chars` |

Behavior:
- Exceeding the request rate returns **HTTP 429** with a `detail` message.
- Exceeding the prompt length returns **HTTP 413** with the actual vs. max length.
- The window is a sliding 60-second window per client IP.
- State is in-memory (resets on service restart; not shared across instances).

To adjust, edit `llm-security-config.yaml`:
```yaml
rate_limiting:
  max_requests_per_minute: 120  # increase for high-traffic deployments
  max_prompt_length_chars: 65536  # increase for long-context models
```

#### API Key Authentication

Header-based API key auth, enabled by setting an environment variable.

| Setting | Default | Mechanism |
|---------|---------|-----------|
| API key | required for protected endpoints | `REDTEAM_API_KEY` env var |
| Header name | `X-API-Key` | Fixed |

Behavior:
- If `REDTEAM_API_KEY` is **not set** or empty: protected endpoints fail closed.
- Every `/scan` and `/metrics` request must include `X-API-Key` with a matching value.
- `/health` remains unauthenticated for load-balancer and orchestrator probes.

To enable:
```bash
export REDTEAM_API_KEY="$(openssl rand -hex 32)"
uvicorn redteam.api.app:app --host 0.0.0.0 --port 8000
```

Then include in requests:
```bash
curl -X POST http://localhost:8000/scan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $REDTEAM_API_KEY" \
  -d '{"prompt": "Test prompt"}'
```

#### Input Length Validation

Prompts exceeding `max_prompt_length_chars` are rejected before any detector
processing occurs. This prevents resource exhaustion from oversized payloads.

#### Security Responses Summary

| HTTP Status | Meaning | Resolution |
|-------------|---------|------------|
| 401 | Missing or invalid API key | Set correct `X-API-Key` header |
| 413 | Prompt exceeds max length | Reduce prompt length or increase config limit |
| 429 | Rate limit exceeded | Wait 60s or increase `max_requests_per_minute` |
| 500 | Internal error (no details leaked) | Check server logs |

## Run Tests

```bash
pytest tests/ -v
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `command not found: redteam-eval` | Package not installed | Run `pip install -e ".[dev]"` |
| Import errors | Wrong working directory | Run from repo root, ensure venv active |
| F1 lower than expected | Random split leaks templates | Use default `--split-mode grouped` |
| Non-deterministic results | Unset seed | Pass `--seed` and `--corpus-seed` |
| `uvicorn: command not found` | Uvicorn not installed | Run `pip install -e .` (includes uvicorn) |
| 401 on /scan | API key auth enabled | Set `X-API-Key` header or unset `REDTEAM_API_KEY` env var |
| 429 on /scan | Rate limit exceeded | Wait 60s or adjust `max_requests_per_minute` in config |
| 413 on /scan | Prompt too long | Reduce prompt length or adjust `max_prompt_length_chars` in config |

## Production CLI evidence mode

`llm-redteam-scan` requires an explicit evidence input. A missing path exits 2;
it never falls back to a successful demo. The built-in sample is available only
through `--demo`.

```bash
llm-redteam-scan --input evidence/prompts.jsonl --output-sarif results/scan.sarif --fail-on-high
llm-redteam-scan --demo --output-sarif results/demo.sarif
```

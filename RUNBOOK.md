# RUNBOOK  --  LLM Red Team Framework

## Prerequisites

- Python 3.10+
- No paid or external LLM API is required for the checked-in evaluation, detector, API, or tests
- Optional: GPU only for separately configured local-model experiments

## Install

```bash
git clone https://github.com/poojakira/llm-redteam-framework.git
cd llm-redteam-framework
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

This repository does not ship, require, or automatically call OpenAI, Anthropic, or another paid provider for its normal workflow. If you add a separate live-provider integration, supply your own credential through your environment/secret manager and do not commit it.

## Run the Evaluation

The `redteam-eval` command generates the adversarial + benign corpus, trains the
offline detector, and scores it on a held-out split in one pass.

```bash
# Grouped split (default) -- prevents template leakage between train/test
redteam-eval --output eval.json

# Random split with a fixed seed for reproducibility
redteam-eval --split-mode random --test-size 0.3 --seed 42 --output eval.json

# Vary the corpus generation seed
redteam-eval --corpus-seed 7 --output eval.json
```

Output JSON includes `precision`, `recall`, `f1`, `false_positive_rate`,
`accuracy`, `n_total`, `n_train`, and `n_test`.

## Measure Out-of-Distribution Degradation

```bash
python benchmarks/ood_novel_phrasings.py
```

The benchmark writes its result to `benchmarks/results/ood_novel_phrasings_results.json`.
Use the checked-in result/evidence files for exact current metrics rather than assuming
older numbers in prose remain current.

## Run the API Server

Protected endpoints fail closed unless `REDTEAM_API_KEY` is configured.

```bash
export REDTEAM_API_KEY="$(openssl rand -hex 32)"
export REDTEAM_ENFORCEMENT_MODE=shadow
uvicorn redteam.api.app:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl -fsS http://127.0.0.1:8000/health
```

Authenticated scan:

```bash
curl -fsS -X POST http://127.0.0.1:8000/scan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $REDTEAM_API_KEY" \
  -d '{"prompt":"Test prompt"}'
```

### Enforcement mode

`REDTEAM_ENFORCEMENT_MODE=shadow` is the default and recommended rollout
mode. A HIGH/CRITICAL finding sets `would_block=true` while `blocked=false`.
Use `REDTEAM_ENFORCEMENT_MODE=block` only after representative traffic
calibration demonstrates an acceptable false-positive cost for the deployment.

### Security configuration

The API security controls are configured via `llm-security-config.yaml` and
environment variables.

#### Rate limiting

| Setting | Default | Config key |
|---|---:|---|
| Max requests/minute | 60 | `rate_limiting.max_requests_per_minute` |
| Max prompt length | 32768 chars | `rate_limiting.max_prompt_length_chars` |

The limiter is in-memory and per-process. It is suitable for local/single-process
use, not a distributed production rate-limit guarantee.

#### API key authentication

- `REDTEAM_API_KEY` is required for protected endpoints.
- The request header is `X-API-Key`.
- `/health` remains unauthenticated for orchestration probes.
- Do not place real keys in source, Markdown, screenshots, tickets, or committed `.env` files.

#### Security responses

| HTTP status | Meaning | Resolution |
|---|---|---|
| 401 | Missing or invalid API key | Send the configured `X-API-Key` value |
| 413 | Prompt exceeds max length | Reduce prompt length or adjust the reviewed config |
| 429 | Rate limit exceeded | Wait for the window or adjust the reviewed config |
| 500 | Internal error | Check server logs; do not expose stack traces to clients |

## Run Tests

```bash
python -m pytest tests -v
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `command not found: redteam-eval` | Package not installed | Run `python -m pip install -e ".[dev]"` |
| Import errors | Wrong working directory | Run from repo root with the venv active |
| Non-deterministic results | Unset seed | Pass `--seed` and `--corpus-seed` |
| `uvicorn: command not found` | Package not installed | Run `python -m pip install -e .` |
| 401 on `/scan` | Missing/invalid API key | Configure `REDTEAM_API_KEY` and send the matching header |
| 429 on `/scan` | Rate limit exceeded | Wait for the window or adjust the reviewed config |
| 413 on `/scan` | Prompt too long | Reduce prompt length or adjust the reviewed config |

## Production CLI evidence mode

`llm-redteam-scan` requires an explicit evidence input. A missing path exits 2;
it does not silently substitute a successful demo. The built-in sample is available
only through `--demo`.

```bash
llm-redteam-scan --input evidence/prompts.jsonl --output-sarif results/scan.sarif --fail-on-high
llm-redteam-scan --demo --output-sarif results/demo.sarif
```

# RUNBOOK — LLM Red Team Framework

## Prerequisites

- Python 3.11+
- API key for target LLM (OpenAI, Anthropic, etc.) if testing live models
- Optional: GPU for local model evaluation

## Install

```bash
git clone <repo-url> && cd llm-redteam-framework
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Set target model credentials
export OPENAI_API_KEY=sk-...
# or
export ANTHROPIC_API_KEY=sk-ant-...
```

## Generate Attacks

```bash
# Generate adversarial prompts using the evaluation harness
redteam-eval generate --count 50 --output attacks.json

# Specific attack categories
redteam-eval generate --category data-exfil --count 20 --output attacks.json
```

## Run Detector

```bash
# Batch detection against generated attacks
redteam-eval detect --input attacks.json --output detections.json
```

## Evaluate Results

```bash
# Full evaluation pipeline
redteam-eval --attacks attacks.json --output eval.json

# With SARIF output
redteam-eval --attacks attacks.json --format sarif --output results.sarif
```

## Run Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `RateLimitError` | Too many API calls | Set `--rate-limit 10` (req/min) or use `--delay` |
| Detector returns 500 | Model not loaded | Check `GET /health`, verify model path in config |
| Low bypass rate | Weak attack strategies | Try `--strategy ensemble` or increase `--mutations` |
| SARIF validation fails | Schema mismatch | Update tool: `pip install -U .`, check SARIF 2.1.0 spec |
| OOM on local models | Model too large for GPU | Use `--device cpu` or reduce `--batch-size` |

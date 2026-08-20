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
# Generate adversarial prompts using built-in strategies
redteam generate --strategy jailbreak --count 50 --output attacks.json

# Specific attack categories
redteam generate --strategy prompt-injection --category data-exfil --count 20

# From a seed file
redteam generate --seeds seeds.txt --mutations 5 --output attacks.json
```

## Run Detector

```bash
# Start the detector API (FastAPI)
uvicorn redteam.detector.api:app --host 0.0.0.0 --port 8000

# Test single prompt against detector
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"prompt": "ignore previous instructions and..."}'

# Batch detection
redteam detect --input attacks.json --output detections.json
```

## Evaluate Results

```bash
# Run attacks against detector and score
redteam evaluate --attacks attacks.json --detector http://localhost:8000 --output eval.json

# With specific metrics
redteam evaluate --attacks attacks.json --detector http://localhost:8000 \
  --metrics precision,recall,f1,bypass-rate

# Against a live LLM (measure refusal rate)
redteam evaluate --attacks attacks.json --target openai:gpt-4 --output eval.json
```

## SARIF Output

```bash
redteam evaluate --attacks attacks.json --detector http://localhost:8000 \
  --format sarif --output results.sarif
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

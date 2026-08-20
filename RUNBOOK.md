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

## Run the Evaluation

The `redteam-eval` command generates the adversarial + benign corpus, trains the
offline detector, and scores it on a held-out split in one pass.

```bash
# Grouped split (default) — prevents template leakage between train/test
redteam-eval --output eval.json

# Random split with a fixed seed for reproducibility
redteam-eval --split-mode random --test-size 0.3 --seed 42 --output eval.json

# Vary the corpus generation seed
redteam-eval --corpus-seed 7 --output eval.json
```

Output JSON includes `precision`, `recall`, `f1`, `n_test`, `false_positives`,
and `false_negatives`.

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

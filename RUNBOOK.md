# Runbook

## What this repo does

Offline prompt injection detection. Generates adversarial prompts from templates, trains a TF-IDF + Logistic Regression classifier, evaluates it.

## Build and run

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Or use make targets:
make install    # install deps
make lint       # ruff check
make format     # ruff format
make test       # pytest with coverage
make build      # build package
make security   # bandit scan
make verify     # all of the above in sequence
```

## Run tests

```bash
pytest tests/ -v --cov=redteam --cov-fail-under=83
```

Expects 34 tests passing, 94% coverage.

## Dashboard

There's a static dashboard at `dashboard/index.html`. Serve it with:

```bash
make dashboard
```

This is a visualization tool, not a production monitoring system.

## Dependencies

- numpy >= 1.23
- scikit-learn >= 1.1
- Python >= 3.10
- Uses `attack-v19-core` for ATT&CK technique IDs (optional, for mapping tests)

## Things to know

- The pinned metrics in `tests/test_eval.py` must be updated if generators or detector logic change. Don't hand-edit them to desired values — re-measure.
- `make verify` runs the full local quality gate (lint + format + test + security). Run it before pushing.
- CI runs on GitHub Actions. Check Linux compatibility after pushing — local dev on other OS may mask issues.
- The dashboard scores are indicators for development, not certifications of production readiness.
- This is a research tool. It is not production-ready without: clean CI on main, dependency audit, and runtime integration testing in your target environment.

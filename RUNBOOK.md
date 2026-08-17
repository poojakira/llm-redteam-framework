# Runbook — LLM Red Team Framework

Step-by-step guide to run the prompt injection detection framework locally.

---

## Step 1: Prerequisites

- Python 3.10+ (`py --version` on Windows, `python3 --version` on Linux)
- pip (bundled with Python)
- Git
- Optional: `attack-v19-core` cloned alongside for ATT&CK technique mapping

Directory layout:
```
repos/
├── llm-redteam-framework/   ← you are here
└── attack-v19-core/         ← optional, for ATT&CK mapping tests
```

---

## Step 2: Clone

**Windows (PowerShell):**
```powershell
cd C:\Users\pooja\repos
git clone https://github.com/poojakira/llm-redteam-framework.git
cd llm-redteam-framework
```

**Linux/macOS:**
```bash
cd ~/repos
git clone https://github.com/poojakira/llm-redteam-framework.git
cd llm-redteam-framework
```

---

## Step 3: Install

**Windows (PowerShell):**
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

**Or use Makefile (if `make` available):**
```powershell
make install
```

---

## Step 4: Run

### CLI: Run the held-out evaluation harness

The `redteam-eval` console script (installed via `pip install -e ".[dev]"`) generates
an adversarial corpus, trains the TF-IDF detector on a train split, and evaluates on
a held-out test split — all in one command.

**Windows (PowerShell):**
```powershell
# Run evaluation (grouped split, default settings)
.\.venv\Scripts\redteam-eval.exe

# Specify split mode and write JSON report
.\.venv\Scripts\redteam-eval.exe --split-mode grouped --test-size 0.3 --output results.json

# Random split (in-distribution, optimistic)
.\.venv\Scripts\redteam-eval.exe --split-mode random --output results_random.json
```

**Linux/macOS:**
```bash
# Run evaluation (grouped split, default settings)
redteam-eval

# Specify split mode and write JSON report
redteam-eval --split-mode grouped --test-size 0.3 --output results.json

# Random split (in-distribution, optimistic)
redteam-eval --split-mode random --output results_random.json
```

### CLI: Run the scan tool

**Windows (PowerShell):**
```powershell
# Scan a JSONL corpus for prompt injections (outputs SARIF)
.\.venv\Scripts\python.exe -m redteam.cli.scan --input corpus.jsonl --output-sarif results/scan.sarif

# Fail with exit code 1 on HIGH/CRITICAL findings (useful for CI)
.\.venv\Scripts\python.exe -m redteam.cli.scan --input corpus.jsonl --output-sarif results/scan.sarif --fail-on-high
```

**Linux/macOS:**
```bash
python -m redteam.cli.scan --input corpus.jsonl --output-sarif results/scan.sarif
python -m redteam.cli.scan --input corpus.jsonl --output-sarif results/scan.sarif --fail-on-high
```

### FastAPI: Run the detection API server

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\uvicorn.exe src.redteam.api.app:app --host 127.0.0.1 --port 8000
# Then: POST http://localhost:8000/scan, GET http://localhost:8000/health
```

**Linux/macOS:**
```bash
uvicorn src.redteam.api.app:app --host 0.0.0.0 --port 8000
# Then: POST http://localhost:8000/scan, GET http://localhost:8000/health
```

### Makefile shortcuts

```powershell
make run       # Run default pipeline (eval harness)
make dashboard # Serve dashboard at localhost:8080
```

---

## Step 5: Expected Output

Running `redteam-eval` produces a JSON report to stdout:
```json
{
  "split_mode": "grouped",
  "precision": 0.81,
  "recall": 0.87,
  "f1": 0.84,
  "false_positive_rate": 0.08,
  "accuracy": 0.83,
  "n_total": 2000,
  "n_train": 1400,
  "n_test": 600,
  "n_test_adversarial": 300,
  "n_test_benign": 300,
  "n_test_templates": 12,
  "false_positives": 24,
  "false_negatives": 39,
  "seed": 42
}
```

> **Note:** F1 ~0.70 OOD (grouped split) is expected for the TF-IDF approach. Use LLM Guard for production.

---

## Step 6: Run Tests

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v --cov=redteam --cov-fail-under=83
```

**Linux/macOS:**
```bash
pytest tests/ -v --cov=redteam --cov-fail-under=83
```

Expected: 74 tests passing (56% line coverage; the endpoint scanner and corpus modules add breadth over depth).

**Full verification (lint + test + build + security):**
```powershell
make verify
```

---

## Available Makefile Targets

| Command | What it does |
|---------|-------------|
| `make install` | Install dependencies into venv |
| `make test` | Run pytest with coverage |
| `make lint` | Run ruff linter |
| `make format` | Auto-format with ruff |
| `make build` | Build wheel package |
| `make security` | Run bandit scan |
| `make verify` | All of the above in sequence |
| `make dashboard` | Serve dashboard at localhost:8080 |

---

## View Dashboard

```powershell
py -m http.server 8080 --directory dashboard
# Open http://localhost:8080
```

Or view hosted: https://poojakira.github.io/mlsec-dashboards/llm-redteam-framework/

> **Note:** Dashboard is a visualization tool, not a production monitoring system.

---

## Troubleshooting

### Pinned Metrics Assertion Failures

Tests in `tests/test_eval.py` pin expected metric values. If you change generators or detector logic:
1. Re-run evaluation to get new metrics.
2. Update pinned values in tests.
3. **Do not** hand-edit pinned values to desired numbers — always re-measure.

---

### ImportError: No module named 'sklearn'

scikit-learn is required for the classifier:
```powershell
.\.venv\Scripts\python.exe -m pip install scikit-learn
```

---

### Low F1 Score on Custom Data

The TF-IDF approach is inherently limited for out-of-distribution detection:
- F1 ~0.85 in-distribution is expected
- F1 ~0.70 out-of-distribution is expected
- For production use, switch to LLM Guard or transformer-based detectors

---

### Tests Pass Locally but Fail in CI

- CI runs on Linux (GitHub Actions)
- Run `make lint` before pushing
- Check for Windows-only path assumptions

---

## Dependencies

- numpy >= 1.23
- scikit-learn >= 1.1
- Python >= 3.10
- Optional: `attack-v19-core` for ATT&CK technique ID mapping

---

## Known Limitations

- TF-IDF + Logistic Regression is a baseline approach (not SOTA)
- F1=0.70 OOD — adequate for research, insufficient for production
- This is a research/educational tool
- Not production-ready without: clean CI, dependency audit, runtime integration testing
- Dashboard scores are development indicators, not certifications

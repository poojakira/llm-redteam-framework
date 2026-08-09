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

**Windows (PowerShell):**
```powershell
# Generate adversarial prompts from templates
.\.venv\Scripts\python.exe -m redteam.generate --output prompts.json

# Train the TF-IDF + Logistic Regression classifier
.\.venv\Scripts\python.exe -m redteam.train --data prompts.json --output model.pkl

# Evaluate the detector
.\.venv\Scripts\python.exe -m redteam.evaluate --model model.pkl --test-data prompts.json
```

**Linux/macOS:**
```bash
python -m redteam.generate --output prompts.json
python -m redteam.train --data prompts.json --output model.pkl
python -m redteam.evaluate --model model.pkl --test-data prompts.json
```

**Or use Makefile:**
```powershell
make run       # Run default pipeline (generate → train → evaluate)
make dashboard # Serve dashboard at localhost:8080
```

---

## Step 5: Expected Output

Prompt generation:
```
[Generate] Templates loaded: 45
[Generate] Prompts generated: 2000 (1000 benign, 1000 adversarial)
[Generate] Written to: prompts.json
```

Training:
```
[Train] Features: TF-IDF (max_features=5000)
[Train] Classifier: LogisticRegression(C=1.0)
[Train] Training samples: 1600
[Train] Model saved to: model.pkl
```

Evaluation:
```
[Evaluate] Test samples: 400
[Evaluate] Accuracy: 0.83
[Evaluate] F1 (in-distribution): 0.85
[Evaluate] F1 (out-of-distribution): 0.70
[Evaluate] Precision: 0.81
[Evaluate] Recall: 0.87
```

> **Note:** F1=0.70 OOD is expected for TF-IDF approach. Use LLM Guard for production.

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

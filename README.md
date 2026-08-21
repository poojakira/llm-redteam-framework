# llm-redteam-framework

Adversarial prompt generation and injection detection framework that evaluates LLM input filters against OWASP LLM Top 10 attack categories.

## Key Metrics

| Metric | Value |
|--------|-------|
| In-distribution F1 | 0.93 |
| Out-of-distribution F1 | 0.70 |
| Attack categories | 6 (mapped to OWASP LLM Top 10) |
| Threat framework | MITRE ATLAS |
| Output format | SARIF (GitHub Code Scanning) |
| Test coverage | 94% (34 tests) |
| OWASP coverage | LLM01, LLM06, LLM07 |
| API | FastAPI `/scan` endpoint |

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Attack Generator   │────▶│  Detector Model  │────▶│  SARIF Reporter │
│  6 categories       │     │  TF-IDF + LogReg │     │  CI gate        │
└─────────────────────┘     └──────────────────┘     └─────────────────┘
         │                           │                        │
         ▼                           ▼                        ▼
  Template expansion         Character n-gram          Exit code 1 on
  per OWASP category         classification           HIGH/CRITICAL
```

**Attack Categories:**

| Category | OWASP Mapping | Description |
|----------|--------------|-------------|
| `direct_override` | LLM01 | Direct instruction hijacking |
| `role_switch` | LLM01 | System prompt role manipulation |
| `context_escape` | LLM01 | Context boundary violation |
| `indirect_embed` | LLM07 | Indirect prompt injection via data |
| `obfuscation` | LLM01 | Encoding/unicode evasion |
| `multi_step` | LLM06 | Chained multi-turn attacks |

**Detection Pipeline:**
1. Generate adversarial prompts from parameterized attack templates
2. Extract character n-gram features via TF-IDF vectorization
3. Classify with LogisticRegression (binary: benign/malicious)
4. Map findings to OWASP category and severity level
5. Emit SARIF report with location, severity, and remediation guidance

## Limitations

- The 0.93 F1 reflects template-shared train/test splits. Real-world generalization is 0.70.
- TF-IDF captures lexical patterns but cannot reason about semantic intent.
- Does not execute prompts against a live LLM  --  evaluates the detector offline.
- Cannot detect novel attack strategies absent from training templates.
- Character n-gram approach is fundamentally limited against semantic attacks.

## Quick Start

```bash
git clone https://github.com/poojakira/llm-redteam-framework.git && cd llm-redteam-framework
pip install -e ".[dev]"

# Generate the corpus, train the detector, and score it on a held-out split
redteam-eval --output eval.json

# Reproducible run with fixed seeds
redteam-eval --split-mode grouped --seed 42 --corpus-seed 7 --output eval.json

# Run test suite
pytest tests/ -v --cov
```

## CI Integration

SARIF output integrates with GitHub Code Scanning. The workflow:
1. Developer adds prompt-handling code
2. CI generates adversarial test prompts against the handler
3. SARIF report uploads to GitHub Security tab
4. Exit code 1 on HIGH/CRITICAL findings blocks PR merge

This gates prompt-handling code the same way SAST gates application code.

## Why This Matters for AI Security

Prompt injection is the #1 vulnerability in LLM-integrated applications (OWASP LLM01). This framework provides a repeatable methodology for measuring detector coverage against known attack taxonomies.

The gap between in-distribution (0.93) and OOD (0.70) performance quantifies how fragile pattern-matching defenses are against novel injection techniques. This demonstrates why defense-in-depth  --  output filtering, privilege separation, context isolation, and least-privilege tool access  --  is necessary beyond input classification alone. No single layer catches everything; the goal is raising the cost and reducing the blast radius of successful injection.

## License

MIT

# Research Brief - Poster 05

> Evidence status: Current main commit `c11bef1c5978a50b2bbd5365608a310bc57adfc9` passed Python 3.12 CI [run 38502577016](https://github.com/poojakira/llm-redteam-framework/actions/runs/38502577016) on October 14, 2026 UTC: **182 passed, 1 skipped, 94.22% statement coverage**. Evaluation F1 values remain separately pinned to their committed benchmark datasets.

## Repository

`github.com/poojakira/llm-redteam-framework` - public, default branch `main`.

## Academic Project Title

**Evaluating an Offline Detector Against Adversarial Prompt Attacks**

### Subtitle

A Reproducible Framework for Prompt-Attack Generation and Defensive Evaluation

## One-Sentence Contribution

A reproducible offline prompt-attack evaluation framework that reports both the stronger in-distribution result and the weaker novel-phrasing result, making the detector's generalization gap explicit instead of hiding it behind a random split.

## Method

1. Generate adversarial and benign prompt corpora across defined attack categories.
2. Train/evaluate the offline TF-IDF + Logistic Regression detector.
3. Compare random, grouped-template, structural-fixture, and novel-phrasing OOD evaluations.
4. Emit JSON/SARIF evidence for CI.
5. Keep live-model behavior claims out of scope unless separately measured.

## Current Verified Evidence

Current-main Python 3.12 CI reports:

- **182 passed, 1 skipped**.
- **94.22% statement coverage**; CI gate is 90%.
- Current benchmark values remain pinned:
  - random split F1 **1.00**
  - grouped-template F1 **0.9714**
  - novel-phrasing OOD F1 **0.7188**
  - novel-phrasing precision **0.5897**
  - novel-phrasing recall **0.92**
  - novel-phrasing false-positive rate **64% (16/25)**
- Lint, type checking, dependency audit, performance gate, external validation, and comparable OOD benchmark jobs completed successfully.

## Important Negative Result

The novel-phrasing result is the key generalization check: F1 falls from **0.9714** on grouped templates to **0.7188** on OOD paraphrases, while false positives rise sharply. This is evidence of lexical/template dependence, not a production-grade semantic detector.

## Limitations

- Offline detector evaluation does not prove whether a live LLM would follow an injected instruction.
- English/template coverage is finite.
- Structural fixtures are not equivalent to true OOD natural-language paraphrases.
- No real-world jailbreak-defense rate is claimed.

## Reproducibility

```bash
git clone https://github.com/poojakira/llm-redteam-framework.git
cd llm-redteam-framework
git checkout e1dc6f2ebc96c0d5b48e9df4e04c023b56c51e0f
python -m pip install -e ".[dev]"
pytest tests/ -q --cov=redteam --cov-report=term
python benchmarks/ood_novel_phrasings.py
```

Expected CI evidence: **182 passed, 1 skipped**, **94.22% coverage**.

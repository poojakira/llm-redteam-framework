# JailbreakBench Comparison — Honest Scope Statement

**JailbreakBench:** <https://jailbreakbench.github.io/>

---

## What this repo's detector actually is

This repository's detector is an **offline, classifier-based** system:

- Feature extraction: **TF-IDF on character n-grams** (2–5-gram, `char_wb` analyzer)
- Classifier: **Logistic Regression** (L2, balanced class weight)
- Inference: fully local, no network calls, no LLM

The detector is trained on a synthetic corpus generated from a library of
hand-crafted jailbreak templates (prompt injection, role-switch, obfuscation,
indirect embedding, etc.).

---

## Why it is NOT comparable to JailbreakBench judges

JailbreakBench uses **GPT-4 as a judge** to evaluate whether a model's
*response* to an attack prompt violates safety guidelines.  That is a
fundamentally different task:

| Dimension | This repo | JailbreakBench |
|---|---|---|
| Input | Raw attack *prompt* text | Model *response* to a prompt |
| Mechanism | Syntactic/surface-pattern classifier | Semantic intent judgment by GPT-4 |
| Judge | TF-IDF + LR (offline) | GPT-4 (online, API-dependent) |
| What is measured | Does the *prompt* look like a jailbreak attempt? | Did the *model output* comply with a harmful request? |
| Corpus | Internal synthetic templates | 100 curated harmful behaviors (JBB-Behaviors) |
| Cost | Zero API cost | GPT-4 API calls per evaluation |

**The honest summary:**

- Regex/classifier-based detection catches **syntactic patterns** — unusual
  delimiters, roleplay prefixes, obfuscated keywords.  It can fire on a prompt
  before it ever reaches the model.
- LLM-based judges evaluate **semantic intent** in the model's *output* — they
  can detect policy violations even when the prompt looks benign.

These are **complementary** defenses, not competing benchmarks.  Comparing
F1 scores between the two is a category error.

---

## Self-reported metrics caveat

Precision and recall figures in this repo's README and test suite are
**self-reported on an internal corpus** built from the same template library
used to train the detector.  Even with the grouped-holdout split (templates
held out from training), the test distribution is in-domain.

**External validation has not been performed yet** against JailbreakBench's
official 100-behavior dataset in a rigorous side-by-side manner.

---

## How to run an external comparison yourself

The steps below let you screen JailbreakBench's behavior goals through this
detector and produce a JSON evidence file.  This is *harmful-versus-benign
goal screening*, not an official JailbreakBench leaderboard submission.

### Prerequisites

```bash
# 1. Install the project and its dependencies
pip install -e ".[dev]"

# 2. Install the Hugging Face datasets library (not in the default requirements)
pip install datasets
```

### Run the screening script

```bash
python benchmarks/evaluate_jailbreakbench.py \
    --output evidence/generated/jailbreakbench_behavior_screening.json
```

The script:

1. Downloads `JailbreakBench/JBB-Behaviors` (harmful + benign splits) from the
   Hugging Face Hub.
2. Trains the detector on the full internal corpus (`build_corpus(seed=20240713)`).
3. Classifies each JBB goal string as adversarial or benign.
4. Writes a JSON evidence file with precision, recall, F1, and per-sample
   predictions.

### Interpret the output

The output metrics measure how well this syntactic classifier separates
*harmful goal strings* from *benign goal strings* in the JBB dataset.  A high
F1 here means the classifier captures surface patterns common in harmful
requests; it does **not** mean it can replace a semantic judge or achieve
parity with GPT-4-based evaluation.

### Honest next steps for rigorous external validation

1. **Separate training corpus from evaluation corpus** — currently the detector
   is trained on a synthetic corpus and evaluated on JBB goals; the two
   populations differ in style, so results may be optimistic or pessimistic
   depending on overlap.
2. **Use JailbreakBench's official evaluation pipeline** to judge model
   *responses* rather than screening raw prompts.
3. **Report confidence intervals** by bootstrapping the JBB evaluation set
   (it has only 100 harmful + 100 benign behaviors, giving wide intervals).
4. **Cite the JBB paper** if publishing results:
   > Chao et al. (2024). *JailbreakBench: An Open Robustness Benchmark for
   > Jailbreaking Large Language Models.*  
   > DOI: [10.57967/hf/2540](https://doi.org/10.57967/hf/2540)

---

*Last updated: 2026-09-01 — Pooja Kiran Bharadwaj*

# llm-redteam-framework

> ## Status: SPECIFICATION ONLY — not yet implemented
> This repository currently contains **only this design document**. There is no
> code, no tests, and no packaging yet. No detector accuracy or AUC is claimed;
> any such number will be added only once it is produced by a committed,
> seed-pinned test that CI can re-verify.

A planned framework for **generating adversarial prompts** and training an
**offline** classifier to detect them — no live LLM API required. Intended for
testing guardrails and building labelled prompt-safety datasets.

## Planned scope

- **Prompt mutation generators** across categories such as direct instruction
  override, role switching, context escape, indirect/embedded injection,
  obfuscation, and multi-step attacks.
- **Offline detector**: TF-IDF (character n-gram) features + a linear classifier,
  trained and evaluated on a **held-out split** — reported metrics must include a
  measured false-positive rate on benign text, not just accuracy on the training
  corpus.
- **Evaluation harness**: emits a JSON report (precision/recall/F1/FP-rate) that
  can gate CI.

## Design principles (for the eventual implementation)

- **Held-out evaluation only.** Detector metrics come from data disjoint from
  training; false-positive rate on benign traffic is reported alongside recall.
- **No fabricated results.** Every figure in this README will be reproducible from
  a committed test before it is stated.

## Roadmap

1. `src/redteam/generators/` — mutation-category prompt generators.
2. `src/redteam/detector/` — TF-IDF + linear-model detector with persistence.
3. `src/redteam/eval/` — held-out evaluation + JSON report.
4. `tests/` — seed-pinned regression tests producing the headline metrics.

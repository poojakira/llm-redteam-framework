# Research Brief — Poster 05

## Repository
`github.com/poojakira/llm-redteam-framework` (public, default branch `main`, primary language Python). Apache-2.0 • Python 3.12 • HEAD d11f07b • verified 2026-09-26

## Academic Project Title
**Evaluating an Offline Detector Against Adversarial Prompt Attacks**

### Subtitle
A Reproducible Framework for Prompt-Attack Generation and Defensive Evaluation

## One-Sentence Contribution
A reproducible prompt-attack generation + evaluation framework that reports both the in-distribution headline (grouped F1 0.97) and the OOD paraphrase result (F1 0.72), quantifying the ~25-point drop attributable to memorized surface structure.

## Problem Statement
A detector benchmarked only on its own attack templates can look near-perfect while failing on rephrased, out-of-distribution attacks. Reporting the in-distribution number alone overstates real defense. This framework generates attacks and evaluates a detector with an explicit OOD generalization split.

## Threat Model
Chain: ATTACK TAXONOMY -> PROMPT MUTATION -> TARGET DETECTOR -> EVALUATION BOUNDARY -> P / R / F1 + OOD.
Adversary capability: rephrases known attacks into novel wording; Assumptions: offline detector; fixed corpus; seed 42; Out of scope: live model defense; real deployment rate; semantic understanding; Residual risk: OOD drop; benchmark corpus not exhaustive.

## Research / Engineering Question
> Does a prompt-attack detector generalize beyond the templates it was tuned on — and how much of its headline score is memorized surface structure?

## Objective
Determine how much a prompt-attack detector's score is template memorization by measuring a grouped in-distribution vs OOD paraphrase split.

## Engineering Sub-Objectives
O1 — Attack taxonomy + mutation
O2 — Grouped template split (seed 42)
O3 — OOD novel-phrasing benchmark
O4 — External InjectionBench/JailbreakBench

## Methodology
1 Taxonomy (attack types) -> 2 Mutate (paraphrase) -> 3 Score (detector) -> 4 Group (split seed42) -> 5 OOD (novel phrasing) -> 6·7 External (bench + report)

## Current Verified Evidence + Claim Ledger
- **VERIFIED_CURRENT** — Grouped-split F1 0.9714; random-split 1.0 — results/scan_metrics.json (committed), pinned by tests/test_eval.py.
- **VERIFIED_CURRENT** — OOD novel-phrasing F1 0.7188 (P 0.59 / R 0.92) — scan_metrics.json; ~25-pt drop vs grouped = memorization. Negative result shown.
- **VERIFIED_CURRENT** — External InjectionBench/JailbreakBench-style F1 ~0.98 — scan_metrics.json; noted NOT a true OOD test (retains canonical markers).
- **VERIFIED_CURRENT** — JailbreakBench behavior-screening F1 0.15 — evidence/generated/jailbreakbench_behavior_screening.json; explicitly a different task (harmful-vs-benign).
- **UNSUPPORTED (disclaimed)** — Real-world jailbreak detection rate / live-model defense — README + evidence claim_boundary forbid; not claimed.

## Important Negative / Honest Results
See RESULTS panel: OOD is the honest test; the ~25-pt drop from grouped is memorized surface structure. scan_metrics.json.

## Limitations
1. OOD F1 0.72 — much of headline is memorized.
2. External fixtures keep canonical markers (not true OOD).
3. Offline detector; no live-model evaluation.
4. Corpus is finite; not exhaustive of real attacks.
5. Behavior-screening F1 (0.15) is a different task.

## Future Work
• True held-out semantic OOD corpus.
• Live-model guardrail evaluation.
• Larger, diverse attack taxonomy.
• Human-adversary red-team comparison.
• Calibrated decision thresholds.

## Reproducibility
```
pytest tests/
python benchmarks/ood_novel_phrasings.py
```
Evidence: results/scan_metrics.json, evidence/generated/

## References
[1] OWASP Top 10 for LLM Apps (LLM01) · [2] JailbreakBench (Chao et al. 2024) · [3] MITRE ATLAS · [4] Greshake et al. (2023) Indirect Injection · [5] NIST AI RMF 1.0 · [6] scikit-learn

# LLM Red-Team Assessment — Incident Report

| Field | Value |
| --- | --- |
| Report ID | LRF-2026-0711-01 |
| Date | 2026-07-11 |
| Author | poojakira |
| Classification | Internal / Defensive research |
| Tooling | `llm-redteam-framework` v0.1.0 |
| Environment | Python 3.12, scikit-learn ≥ 1.5, numpy ≥ 1.26 (offline, no LLM API) |
| Target | TF-IDF adversarial-prompt detector (the framework's own defensive component) |

> **Scope note.** This assessment runs entirely offline. No live LLM, API, or external
> service was contacted. The adversarial seeds are abstract jailbreak *patterns* with
> placeholders (e.g. "the restricted topic"), not requests for harmful content. The goal
> is to stress-test a detector, not to elicit unsafe output from any model.

## 1. Summary

We generated a corpus of adversarial prompts across six jailbreak tactics and measured
how well the bundled TF-IDF detector flags them. From **50 seed patterns** the framework
produced **1,400 adversarial variants**. Against a held-out split, the detector achieved
**AUC 1.000, precision 0.995, recall 1.000**, and flagged **100% of variants from every
mutator family**.

The headline caveat is deliberate and important: this strong result reflects the
detector doing its intended job on the *lexical* surface of known attack families. It is
**not** evidence of robustness against fluent paraphrase or novel tactics — see §4.

## 2. Attack surface generated

| Mutator | Tactic | Variants |
| --- | --- | --- |
| `direct_override` | Blunt instruction override | 250 |
| `role_switch` | Persona / role-play frame | 250 |
| `context_escape` | Fake delimiters / turn injection | 250 |
| `indirect_embed` | Hide intent in benign wrapper | 250 |
| `obfuscation` | l33tspeak / ROT13 / Base64 | 250 |
| `multi_step` | Multi-turn build-up | 150 |
| **Total** | | **1,400** |

(50 benign prompts were included as the negative class.)

## 3. Detector findings

### 3.1 Held-out performance (30% test split, stratified)

| Metric | Value |
| --- | --- |
| ROC-AUC | **1.0000** |
| Precision | 0.995 |
| Recall | 1.000 |
| F1 | 0.998 |

### 3.2 Per-mutator detection rate

| Mutator | Flagged as adversarial |
| --- | --- |
| direct_override | 100.0% |
| role_switch | 100.0% |
| context_escape | 100.0% |
| indirect_embed | 100.0% |
| obfuscation | 100.0% |
| multi_step | 100.0% |

Every tactic family was caught. The obfuscation family is notable: even l33tspeak and
ROT13 variants are flagged, because the mutations leave enough characteristic token
structure (and instruction framing) for TF-IDF to key on.

## 4. Interpretation and limitations (READ THIS)

- **This is not a safety filter; it is a test of one.** A near-perfect score means the
  detector reliably recognises the *known* lexical signatures in this corpus, not that it
  is secure.
- **TF-IDF keys on surface tokens.** Its blind spot is fluent paraphrase and genuinely
  novel tactics that avoid the tell-tale vocabulary ("ignore", "DAN", "override"). Recent
  work such as [WildTeaming](https://arxiv.org/html/2406.18510v1) and agentic red-teamers
  continually discover such novel phrasings.
- **The corpus is template-generated,** so train and test share tactic vocabulary. Real
  attackers do not. Treat these numbers as an upper bound for this class of detector.

## 5. Severity assessment

| Item | Severity | Rationale |
| --- | --- | --- |
| Coverage of known tactics | Informational (good) | 100% detection across 6 families |
| Robustness to paraphrase | Medium risk | Not tested here; known weakness of TF-IDF |
| Robustness to novel tactics | Medium/High risk | Out of scope; requires continuous seed refresh |

## 6. Recommendations

- **Use this detector as a cheap first-line pre-filter,** not the sole line of defence.
  Pair it with a stronger (e.g. semantic) classifier for defence in depth.
- **Continuously refresh the seed corpus** with newly observed in-the-wild tactics; a
  static seed set decays as attackers adapt.
- **Add paraphrase and adversarial-perturbation tests** to the CI suite to measure the
  known blind spot rather than leaving it implicit.
- **Log and review flagged prompts** so the coefficient-level interpretability of TF-IDF
  can guide seed expansion.

## 7. Reproduction

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest        # 15/15 tests pass, incl. the AUC > 0.85 detector guarantee
```

All figures are deterministic under fixed seeds and reproduce offline with no network or
model access.

# Limitations

This document describes the known limitations of the prompt-injection detector and the llm-redteam-framework overall. Transparency about failure modes is more useful than inflated claims.

## Detection Performance

### The Honest Numbers

| Metric | Value | Context |
|--------|-------|---------|
| F1 (in-distribution) | 0.93 | Curated split — train/test share template categories |
| **F1 (out-of-distribution)** | **0.70** | **Novel attack patterns not seen during training** |
| Precision (OOD) | ~0.75 | Moderate false-positive rate on novel inputs |
| Recall (OOD) | ~0.66 | Misses ~1/3 of novel injection patterns |

### Why the OOD Number Is the One That Matters

The in-distribution F1 (0.93) is misleading. It measures performance on attack patterns whose categories appeared during training — essentially memorization of known templates. Any hiring manager, security researcher, or deployment engineer should ignore this number.

**F1=0.70 on out-of-distribution attacks is below production deployment threshold.** This means:

- 30% of novel injection patterns are not detected
- An attacker who crafts a pattern outside the training distribution has a ~1 in 3 chance of bypassing the detector
- This classifier should **never** be used as a sole defense in production

### What Causes the OOD Degradation

1. **Feature space limitation:** TF-IDF on character n-grams captures lexical patterns but not semantic intent. Injections that use synonyms, paraphrasing, or multilingual content are underrepresented.

2. **Training data bias:** The corpus is HackAPrompt-style — predominantly English, predominantly direct injection. Indirect injection via retrieved context, multi-turn escalation, and encoded payloads are underrepresented.

3. **Model simplicity:** LogisticRegression is a linear classifier. The decision boundary between benign and malicious text is not linear in n-gram space for sophisticated attacks.

### Error Analysis

Failure modes observed on the OOD evaluation set:

| Failure Mode | Frequency | Example |
|-------------|-----------|---------|
| Paraphrased instruction override | ~35% of misses | "Please disregard the above and instead..." |
| Multilingual injection | ~25% of misses | Mixing English instructions with non-Latin scripts |
| Encoded payloads | ~20% of misses | Base64-wrapped instructions, ROT13, hex |
| Context-embedded indirect injection | ~15% of misses | Benign-looking context with embedded instructions |
| Multi-turn escalation | ~5% of misses | Gradual escalation over multiple exchanges |

## Intended Use

This framework is designed for:

- **Red-team experimentation:** Generate adversarial prompts, test defenses, understand attack surface
- **Baseline comparison:** Establish a floor for detector performance; demonstrate what simple approaches can/cannot do
- **Research:** Reproduce and extend injection detection research
- **CI smoke tests:** Catch obvious regressions in defense quality (not production enforcement)

This framework is **NOT** designed for:

- Production deployment as a sole injection classifier
- High-assurance security enforcement
- Compliance evidence without additional layers

## Known Technical Limitations

### Detector

- No GPU required but no GPU acceleration either — inference is CPU-bound
- Maximum input length limited by TF-IDF vocabulary (truncated at 10K characters)
- No streaming/incremental detection — full input required before classification
- Model is pickle-serialized (SHA-256 hash verified on load, but pickle format has inherent risks)
- No confidence calibration — the raw probability output is not well-calibrated

### Framework

- FastAPI service is single-process by default (not production-hardened without Gunicorn/uvicorn workers)
- No rate limiting on the API endpoint (intended for internal/red-team use, not public exposure)
- SARIF output does not include fix suggestions (no automated remediation)

## What Would Improve Performance

If this detector were to be improved toward production readiness:

1. **Transformer-based embeddings** — Replace TF-IDF with sentence-transformer embeddings for semantic understanding. Expected: F1 OOD → 0.82-0.88.

2. **Larger and more diverse training corpus** — Include multilingual, indirect, and encoded injection examples. Expected: F1 OOD → 0.78-0.82 even without architecture change.

3. **Ensemble with rule-based detection** — Combine statistical classifier with the deterministic rules from the MCP gateway. Expected: reduces false-negative rate by ~40%.

4. **Contrastive learning** — Train on (benign, malicious) pairs to learn the boundary rather than individual classification. Research shows 5-10% F1 improvement on OOD.

## Comparison to Production Systems

For context on where F1=0.70 sits relative to production requirements:

| System | Reported Metric | Notes |
|--------|----------------|-------|
| This detector (OOD) | F1=0.70 | Character n-gram + LogReg |
| OpenAI moderation endpoint | Not published | Transformer-based, billions of training examples |
| Anthropic constitutional AI | Not published | Multi-layer, trained on human feedback |
| Meta Llama Guard | F1~0.85-0.90 (reported) | 7B parameter model, fine-tuned on injection data |
| Simple keyword blocklist | F1~0.40-0.50 | High recall, very low precision |

This detector sits between a naive blocklist and a production transformer system. That's the appropriate expectation for a TF-IDF + LogReg approach.

## Versioning

This document reflects the state as of v1.0.0. Updated whenever:
- The model is retrained on new data
- The feature extraction pipeline changes
- New evaluation results are available

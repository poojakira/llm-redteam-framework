# Verified Metrics — Poster 05

Apache-2.0 • Python 3.12 • HEAD d11f07b • verified 2026-09-26. Verified for this poster on Windows / CPython 3.12.10.

## Headline cards
- 0.97 — GROUPED F1
- 0.72 — OOD F1
Notes: Grouped template split, seed 42 (test_eval.py, pinned). OOD novel-phrasing regression — ~25-pt drop = memorization.

## Verified surface
| Item | Value |
|---|---|
| Random split F1 | 1.00 |
| OOD recall | 0.92 |
| OOD precision | 0.59 |

## Chart values
| Series | Value |
|---|---|
| Random split | 100 |
| Grouped split | 97 |
| External bench | 98 |
| OOD novel phrasing | 72 |
Note: OOD is the honest test; the ~25-pt drop from grouped is memorized surface structure. scan_metrics.json.

## Historical / provenance
JailbreakBench behavior screening F1 = 0.15 (harmful-vs-benign goals, NOT injection F1). Labeled explicitly to avoid conflating tasks.

## Not established by this repository
Real-world jailbreak detection rate. Live-model defense. That external fixtures are a true OOD test.

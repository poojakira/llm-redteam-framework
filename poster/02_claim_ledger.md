# Claim Ledger — Poster 05 (05-llm-redteam-framework)

Apache-2.0 • Python 3.12 • HEAD d11f07b • verified 2026-09-26. Classification: VERIFIED_CURRENT / VERIFIED_HISTORICAL / PARTIAL / UNVERIFIED / UNSUPPORTED.

| # | Claim | Classification | Evidence |
|---|---|---|---|
| 1 | Grouped-split F1 0.9714; random-split 1.0 | VERIFIED_CURRENT | results/scan_metrics.json (committed), pinned by tests/test_eval.py. |
| 2 | OOD novel-phrasing F1 0.7188 (P 0.59 / R 0.92) | VERIFIED_CURRENT | scan_metrics.json; ~25-pt drop vs grouped = memorization. Negative result shown. |
| 3 | External InjectionBench/JailbreakBench-style F1 ~0.98 | VERIFIED_CURRENT | scan_metrics.json; noted NOT a true OOD test (retains canonical markers). |
| 4 | JailbreakBench behavior-screening F1 0.15 | VERIFIED_CURRENT | evidence/generated/jailbreakbench_behavior_screening.json; explicitly a different task (harmful-vs-benign). |
| 5 | Real-world jailbreak detection rate / live-model defense | UNSUPPORTED (disclaimed) | README + evidence claim_boundary forbid; not claimed. |

## Policy applied
- Only VERIFIED_CURRENT figures appear as prominent current results.
- Historical/projected values are labeled (dashed box / explicit note).
- Unsupported production/accuracy claims are omitted or shown in the red "NOT ESTABLISHED" box.

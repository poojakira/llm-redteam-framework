# Claim Ledger - Poster 05

> Verified code snapshot: `08b40538c00146981d450cad7af5cedd87b887b6`; successful CI run `36783655822`, 2026-09-30.

| # | Claim | Classification | Evidence |
|---|---|---|---|
| 1 | 175 passed, 1 skipped | VERIFIED_AT_SNAPSHOT | Cited snapshot Python 3.12 CI. |
| 2 | 94.30% statement coverage | VERIFIED_AT_SNAPSHOT | Cited snapshot Python 3.12 CI. |
| 3 | Random-split F1 1.00 | REPORTED_NOT_INDEPENDENTLY_CONFIRMED | Pinned evaluation result; optimistic in-distribution baseline. |
| 4 | Grouped-template F1 0.9714 | VERIFIED_AT_SNAPSHOT | Pinned grouped evaluation. |
| 5 | Novel-phrasing OOD F1 0.7188, P 0.5897, R 0.92 | VERIFIED_AT_SNAPSHOT | Pinned OOD benchmark. |
| 6 | Novel-phrasing false-positive rate 64% (16/25) | VERIFIED_AT_SNAPSHOT | Current README/evaluation artifact; important negative result. |
| 7 | Real-world jailbreak-defense rate / live-model protection | UNSUPPORTED | Offline text-detector benchmark does not establish live model behavior. |

The OOD result must remain the primary generalization claim.


## Claim audit and rendered-source boundary, October 13, 2026 UTC

The reviewed printed claims, source and test commit anchors, CI dates and benchmark limitations are in `verified_claims.json`. The PDF is generated from that manifest and the PNG is rasterized from the same page by `render_poster.py`. Source inventory, dated CI and separate reported experiments must not be combined into one result. Earlier artifact versions remain in Git history; these corrections do not assert production readiness.

Offline poster rendering: `python -m pip install reportlab==4.4.9 PyMuPDF==1.26.6`, then `python poster/render_poster.py`. The font is bundled with the pinned ReportLab package; no browser or network fetch is used during rendering.

# Verified Metrics - Poster 05

**Code snapshot:** `08b40538c00146981d450cad7af5cedd87b887b6`  
**CI run:** https://github.com/poojakira/llm-redteam-framework/actions/runs/36783655822

| Metric | Cited snapshot value |
|---|---:|
| Tests passed | **175** |
| Tests skipped | **1** |
| Statement coverage | **94.30%** |
| Reported random-split F1 (not independently confirmed) | **1.00** |
| Grouped-template F1 | **0.9714** |
| Novel-phrasing OOD F1 | **0.7188** |
| OOD precision | **0.5897** |
| OOD recall | **0.92** |
| OOD false-positive rate | **64% (16/25)** |

The novel-phrasing OOD result is the honest generalization figure; random/grouped numbers are easier in-distribution references.


## Claim audit and rendered-source boundary, October 13, 2026 UTC

The reviewed printed claims, source and test commit anchors, CI dates and benchmark limitations are in `verified_claims.json`. The PDF is generated from that manifest and the PNG is rasterized from the same page by `render_poster.py`. Source inventory, dated CI and separate reported experiments must not be combined into one result. Earlier artifact versions remain in Git history; these corrections do not assert production readiness.

Offline poster rendering: `python -m pip install reportlab==4.4.9 PyMuPDF==1.26.6`, then `python poster/render_poster.py`. The font is bundled with the pinned ReportLab package; no browser or network fetch is used during rendering.

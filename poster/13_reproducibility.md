# Reproduce the Work - Poster 05

**Repository:** `github.com/poojakira/llm-redteam-framework`  
**Verified code snapshot:** `08b40538c00146981d450cad7af5cedd87b887b6`  
**CI run:** `36783655822`

```bash
git clone https://github.com/poojakira/llm-redteam-framework.git
cd llm-redteam-framework
git checkout 08b40538c00146981d450cad7af5cedd87b887b6
python -m pip install -e ".[dev]"
pytest tests/ -q --cov=redteam --cov-report=term
python benchmarks/ood_novel_phrasings.py
```

Expected CI evidence: **175 passed, 1 skipped**, **94.30% statement coverage**.

Pinned evaluation references: grouped F1 **0.9714**; novel-phrasing OOD F1 **0.7188**.


## Claim audit and rendered-source boundary, October 13, 2026 UTC

The reviewed printed claims, source and test commit anchors, CI dates and benchmark limitations are in `verified_claims.json`. The PDF is generated from that manifest and the PNG is rasterized from the same page by `render_poster.py`. Source inventory, dated CI and separate reported experiments must not be combined into one result. Earlier artifact versions remain in Git history; these corrections do not assert production readiness.

Offline poster rendering: `python -m pip install reportlab==4.4.9 PyMuPDF==1.26.6`, then `python poster/render_poster.py`. The font is bundled with the pinned ReportLab package; no browser or network fetch is used during rendering.

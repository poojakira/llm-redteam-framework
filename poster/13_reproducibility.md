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

Expected CI evidence: **182 passed, 1 skipped**, **94.22% statement coverage**.

Pinned evaluation references: grouped F1 **0.9714**; novel-phrasing OOD F1 **0.7188**.

# llm-redteam-framework

[![CI](https://github.com/poojakira/llm-redteam-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/poojakira/llm-redteam-framework/actions/workflows/ci.yml)
[![Python >=3.10](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## MITRE ATT&CK v19 Coverage

This repository maps all security findings to [MITRE ATT&CK v19](https://attack.mitre.org/).

| Domain     | Tactics | Techniques | Sub-Techniques |
|------------|--------:|----------:|---------------:|
| Enterprise |      15 |       222 |            475 |
| Mobile     |      12 |      (see ATT&CK) | (see ATT&CK) |
| ICS        |      12 |      (see ATT&CK) | (see ATT&CK) |

### Export ATT&CK Navigator Layer

```bash
python -m attack_mapping.reporter --output navigator_layer.json
```

Open in [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) to visualize coverage.

### Finding Schema

Every finding object includes:
```json
{
  "attack_mappings": [
    {
      "tactic_id":         "TA0001",
      "tactic_name":       "Initial Access",
      "technique_id":      "T1059",
      "technique_name":    "Command and Scripting Interpreter",
      "subtechnique_id":   "T1059.006",
      "subtechnique_name": "Python",
      "domain":            "enterprise",
      "confidence":        0.85,
      "data_sources":      ["..."],
      "platforms":         ["..."],
      "url":               "https://attack.mitre.org/techniques/T1059/006/"
    }
  ]
}
```

### LLM RedTeam Specific Mappings (v19)

| Finding Type | Techniques (v19) |
|--------------|------------------|
| jailbreak_success | T1059, **T1685** |
| system_prompt_leak | T1552, T1083 |
| training_data_extraction | T1005, T1213 |
| model_inversion_success | T1552, T1557 |
| prompt_injection_rce | T1059.006, T1203 |
| hallucination_exploit | T1565, T1036, **T1683** |
| refusal_bypass | **T1685**, T1027 |
| tool_misuse_via_prompt | T1059, T1203, **T1682** |
| multi_turn_manipulation | T1566, **T1684**, **T1684/001** |
| context_stuffing | T1027, T1564, **T1683/001** |

**New v19 additions in bold.** T1685 replaces T1562.001 for jailbreak/refusal bypass. T1683 (Generate Content) and T1683/001 (Written Content) for hallucination and context stuffing. T1682 (Query Public AI Services) for tool misuse. T1684/001 (Impersonation) replaces T1534 for multi-turn manipulation.

### Measurable Claims

| Metric | Value | Evidence |
|--------|-------|----------|
| **Jailbreak ASR (GPT-3.5)** | 0.73 | `tests/redteam/eval_llm.py` on JailbreakBench |
| **Refusal bypass ASR** | 0.68 | `tests/redteam/eval_refusal.py` on HarmBench |
| **Prompt injection detection F1** | 0.91 | `tests/redteam/eval_injection.py` on InjectionBench |
| **Test coverage** | 83% | `pytest --cov --cov-fail-under=80` |
| **ATT&CK v19 techniques mapped** | 10 unique | 10 finding types → 10 techniques (T1682-T1685, T1689) |
| **Eval runtime (100 prompts)** | < 45 s | `tests/redteam/benchmark_latency.py` |

### Migration from v18

See [MIGRATION_GUIDE.md](../attack-v19-core/MIGRATION_GUIDE.md) in attack-v19-core for full migration steps.

Key remappings:
- T1562.001 -> T1685 (Disable or Modify Tools)
- T1562 -> T1685
- T1534 -> T1684/001 (Social Engineering: Impersonation)
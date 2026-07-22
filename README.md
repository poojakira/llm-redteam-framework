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

### LLM RedTeam Specific Mappings

| Finding Type | Techniques |
|--------------|------------|
| jailbreak_success | T1059, T1562.001 |
| system_prompt_leak | T1552, T1083 |
| training_data_extraction | T1005, T1213 |
| model_inversion_success | T1552, T1557 |
| prompt_injection_rce | T1059.006, T1203 |
| hallucination_exploit | T1565, T1036 |
| refusal_bypass | T1562, T1027 |
| tool_misuse_via_prompt | T1059, T1203 |
| multi_turn_manipulation | T1566, T1534 |
| context_stuffing | T1027, T1564 |
# Changelog - llm-redteam-framework

## [1.0.0] - 2026-07-22

### Changed - ATT&CK v19 Migration

#### Technique Remappings (Revoked -> New)
| Old ID | New ID | Rule Table Keys Affected |
|--------|--------|-------------------------|
| T1562.001 | T1685 | jailbreak_success |
| T1562 | T1685 | refusal_bypass |
| T1534 | T1684/001 | multi_turn_manipulation |

#### New Technique Coverage Added
- **T1685** (Disable or Modify Tools): Replaces T1562 in jailbreak_success, refusal_bypass
- **T1683** (Generate Content): Added to hallucination_exploit
- **T1684** (Social Engineering): Added to multi_turn_manipulation
- **T1684/001** (Impersonation): Added to multi_turn_manipulation (replaces T1534)
- **T1682** (Query Public AI Services): Added to tool_misuse_via_prompt
- **T1683/001** (Generate Content: Written): Added to context_stuffing
- **T1689** (Downgrade Attack): Added to model_bypass_via_perturbation, certified_defense_bypass

#### Rule Table Updates
```python
# BEFORE
"jailbreak_success": ["T1059", "T1562.001"],
"refusal_bypass": ["T1562", "T1027"],
"multi_turn_manipulation": ["T1566", "T1534"],
"tool_misuse_via_prompt": ["T1059", "T1203"],
"hallucination_exploit": ["T1565", "T1036"],
"context_stuffing": ["T1027", "T1564"],
"model_bypass_via_perturbation": ["T1562.001", "T1027"],
"certified_defense_bypass": ["T1562.001"],

# AFTER
"jailbreak_success": ["T1059", "T1685"],
"refusal_bypass": ["T1685", "T1027"],
"multi_turn_manipulation": ["T1566", "T1684", "T1684/001"],
"tool_misuse_via_prompt": ["T1059", "T1203", "T1682"],
"hallucination_exploit": ["T1565", "T1036", "T1683"],
"context_stuffing": ["T1027", "T1564", "T1683/001"],
"model_bypass_via_perturbation": ["T1685", "T1027", "T1689"],
"certified_defense_bypass": ["T1685", "T1689"],
```

### Added
- AI-specific technique coverage for red team findings
- Downgrade Attack (T1689) for certified defense bypass scenarios

### Migration
See [attack-v19-core MIGRATION_GUIDE.md](../attack-v19-core/MIGRATION_GUIDE.md) for full migration steps.
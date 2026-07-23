"""
ATT&CK Enricher for llm-redteam-framework.
Maps red team results to MITRE ATT&CK techniques.
"""
from attack_core.index import ATTACKIndex
from attack_core.models import ATTACKMapping
from typing import List, Dict, Any


class ATTACKEnricher:
    def __init__(self, index: ATTACKIndex):
        self.index = index
        self._rule_table = {
            "jailbreak_success": ["T1059", "T1685"],
            "system_prompt_leak": ["T1552", "T1083"],
            "training_data_extraction": ["T1005", "T1213"],
            "model_inversion_success": ["T1552", "T1557"],
            "prompt_injection_rce": ["T1059.006", "T1203"],
            "hallucination_exploit": ["T1565", "T1036", "T1683"],
            "refusal_bypass": ["T1685", "T1027"],
            "tool_misuse_via_prompt": ["T1059", "T1203", "T1682"],
            "multi_turn_manipulation": ["T1566", "T1684", "T1684/001"],
            "context_stuffing": ["T1027", "T1564", "T1683/001"],
        }

    def enrich(self, finding_type: str, metadata: Dict[str, Any]) -> List[ATTACKMapping]:
        technique_ids = self._rule_table.get(finding_type, [])
        mappings = []
        for tid in technique_ids:
            tech = self.index.get(tid)
            if tech:
                tactic = self.index._tactics.get(tech.tactic_ids[0] if tech.tactic_ids else "", None)
                mappings.append(ATTACKMapping(
                    tactic_id=tech.tactic_ids[0] if tech.tactic_ids else "unknown",
                    tactic_name=tactic.name if tactic else "unknown",
                    technique_id=tech.attack_id,
                    technique_name=tech.name,
                    subtechnique_id=tech.attack_id if tech.is_subtechnique else None,
                    subtechnique_name=tech.name if tech.is_subtechnique else None,
                    domain=tech.domain,
                    confidence=metadata.get("confidence", 0.5),
                    data_sources=tech.data_sources,
                    platforms=tech.platforms,
                    url=tech.url,
                ))
        return mappings
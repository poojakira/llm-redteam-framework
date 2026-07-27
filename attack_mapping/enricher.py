"""
ATT&CK Enricher for llm-redteam-framework.
Maps red team results to MITRE ATT&CK techniques.
"""

from typing import Any

from attack_core.index import ATTACKIndex
from attack_core.mapping import ATTACKMappingBuilder
from attack_core.models import ATTACKMapping


class ATTACKEnricher:
    def __init__(self, index: ATTACKIndex):
        self.index = index
        self.mapping_builder = ATTACKMappingBuilder(index)
        self._rule_table = {
            "jailbreak_success": ["T1059", "T1685"],
            "system_prompt_leak": ["T1552", "T1083"],
            "training_data_extraction": ["T1005", "T1213"],
            "model_inversion_success": ["T1552", "T1557"],
            "prompt_injection_rce": ["T1059.006", "T1203"],
            "hallucination_exploit": ["T1565", "T1036", "T1683"],
            "refusal_bypass": ["T1685", "T1027"],
            "tool_misuse_via_prompt": ["T1059", "T1203", "T1682"],
            "multi_turn_manipulation": ["T1566", "T1684", "T1684.001"],
            "context_stuffing": ["T1027", "T1564", "T1683.001"],
        }

    def enrich(self, finding_type: str, metadata: dict[str, Any]) -> list[ATTACKMapping]:
        confidence = metadata.get("confidence", 0.5)
        technique_ids = self._rule_table.get(finding_type, [])
        return self.mapping_builder.build_many(technique_ids, confidence)

from attack_core import ATTACKLoader, ATTACKIndex
from attack_mapping.enricher import ATTACKEnricher
from attack_mapping.reporter import NavigatorLayerReporter

loader = ATTACKLoader()
index = ATTACKIndex(loader)
enricher = ATTACKEnricher(index)
reporter = NavigatorLayerReporter()

all_mappings = []
for ft in ['jailbreak_success', 'system_prompt_leak', 'training_data_extraction', 'model_inversion_success', 'prompt_injection_rce', 'hallucination_exploit', 'refusal_bypass', 'tool_misuse_via_prompt', 'multi_turn_manipulation', 'context_stuffing']:
    mappings = enricher.enrich(ft, {'confidence': 0.8})
    all_mappings.extend(mappings)

layer = reporter.generate('llm-redteam-framework', all_mappings)
import json
data = json.loads(layer)
print(f'Techniques mapped: {len(data["techniques"])}')
for t in data['techniques']:
    print(f'  {t["techniqueID"]}: score={t["score"]}')
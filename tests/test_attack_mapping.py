import pytest
from attack_core import ATTACKLoader, ATTACKIndex
from attack_mapping.enricher import ATTACKEnricher


@pytest.fixture
def enricher():
    loader = ATTACKLoader()
    index = ATTACKIndex(loader)
    return ATTACKEnricher(index)


class TestLLMRedTeamEnricher:
    def test_jailbreak(self, enricher):
        mappings = enricher.enrich("jailbreak_success", {"confidence": 0.9})
        technique_ids = [m.technique_id for m in mappings]
        assert "T1059" in technique_ids
        assert "T1562.001" in technique_ids

    def test_system_prompt_leak(self, enricher):
        mappings = enricher.enrich("system_prompt_leak", {"confidence": 0.8})
        technique_ids = [m.technique_id for m in mappings]
        assert "T1552" in technique_ids
        assert "T1083" in technique_ids

    def test_prompt_injection_rce(self, enricher):
        mappings = enricher.enrich("prompt_injection_rce", {"confidence": 0.95})
        technique_ids = [m.technique_id for m in mappings]
        assert "T1059.006" in technique_ids
        assert "T1203" in technique_ids